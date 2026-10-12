"""Divergence engine: index, routing, conservation, distance."""
import numpy as np
import pandas as pd

from models.divergence import (divergence_index, haversine_km,
                               route_between_cities, route_within_city)


def _zones(demand, alloc):
    return pd.DataFrame({
        "zone_id": [f"Z{i}" for i in range(len(demand))],
        "pred_daily_kl": demand, "supply_kl": alloc,
        "balance_kl": np.array(alloc) - np.array(demand),
        "shortage_kl": np.clip(np.array(demand) - np.array(alloc), 0, None),
        "excess_kl": np.clip(np.array(alloc) - np.array(demand), 0, None),
        "shortage_risk": np.clip((np.array(demand) - np.array(alloc)) / np.array(demand), 0, None),
    })


def test_divergence_index_zero_when_matched():
    assert divergence_index([0.0, 0.0], 100.0) == 0.0


def test_divergence_index_positive_when_unbalanced():
    assert divergence_index([50.0, -50.0], 100.0) > 0


def test_within_city_routing_moves_surplus_to_deficit():
    z = _zones([100.0, 100.0], [150.0, 50.0])       # Z0 surplus 50, Z1 deficit 50
    out = route_within_city(z)
    assert out["scope"] == "within-city"
    assert out["delivered_kl"] > 0
    assert out["residual_shortage_kl"] < out["total_shortage_kl"]
    for t in out["transfers"]:
        assert t["delivered_kl"] <= t["sent_kl"] + 1e-9   # losses are non-negative


def test_within_city_never_over_donates():
    z = _zones([100.0, 100.0], [200.0, 0.0])
    out = route_within_city(z)
    sent = sum(t["sent_kl"] for t in out["transfers"])
    assert sent <= 100.0 * 0.70 + 1e-6        # only TRANSFER_MAX_FRACTION_OF_SURPLUS


def test_haversine_reasonable():
    # Mumbai -> Pune ~ 120 km
    d = haversine_km(19.076, 72.8777, 18.5204, 73.8567)
    assert 100 < d < 160


def test_between_city_respects_distance_cap():
    states = [
        {"city": "A", "lat": 19.0, "lon": 72.8, "residual_shortage_kl": 0.0, "surplus_kl": 100000.0},
        {"city": "B", "lat": 19.1, "lon": 72.9, "residual_shortage_kl": 5000.0, "surplus_kl": 0.0},
        {"city": "C", "lat": 28.6, "lon": 77.2, "residual_shortage_kl": 5000.0, "surplus_kl": 0.0},  # far
    ]
    out = route_between_cities(states)
    to_cities = {t["to_city"] for t in out["transfers"]}
    assert "B" in to_cities
    assert "C" not in to_cities          # beyond the distance cap
