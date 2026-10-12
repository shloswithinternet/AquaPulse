"""Redistribution optimiser: feasibility and constraint respect."""
import numpy as np
import pandas as pd

from models.redistribution import optimise_allocation, redistribute


def _zones(demand, supply_kl):
    z = pd.DataFrame({
        "city": ["X"] * len(demand), "state_ut": ["S"] * len(demand),
        "zone_id": [f"Z{i}" for i in range(len(demand))],
        "lat": [0.0] * len(demand), "lon": [0.0] * len(demand),
        "pred_daily_kl": demand, "pred_peak_kl": np.array(demand) / 24,
        "obs_daily_kl": demand,
    })
    from models.shortage import compute_shortage, city_shortage_flags
    z = compute_shortage(z, supply_kl / 1000.0)
    return city_shortage_flags(z)


def test_allocation_respects_supply_and_demand():
    z = _zones([100.0, 100.0, 100.0], supply_kl=200.0)
    alloc, unmet, total_unmet, status = optimise_allocation(z["pred_daily_kl"].to_numpy(), 200.0)
    assert status == "optimal"
    assert alloc.sum() <= 200.0 + 1e-6
    assert (alloc <= z["pred_daily_kl"].to_numpy() * 1.15 + 1e-6).all()
    assert (alloc >= z["pred_daily_kl"].to_numpy() * 0.60 - 1e-6).all()
    assert total_unmet >= 0


def test_unmet_equals_demand_minus_alloc():
    d = np.array([120.0, 80.0, 60.0])
    alloc, unmet, _, _ = optimise_allocation(d, supply_kl=150.0)
    assert np.allclose(unmet, np.clip(d - alloc, 0, None))


def test_priority_shifts_allocation():
    d = np.array([100.0, 100.0])
    a, _, _, _ = optimise_allocation(d, 150.0, priority=np.array([5.0, 1.0]))
    assert a[0] > a[1]


def test_cost_mode_still_respects_supply():
    d = np.array([100.0, 100.0, 100.0])
    alloc, unmet, total, status = optimise_allocation(
        d, 250.0, mode="cost", cost_per_kl=np.array([20.0, 5.0, 10.0]), lambda_cost=0.5)
    assert status == "optimal"
    assert alloc.sum() <= 250.0 + 1e-6


def test_redistribute_frame_adds_columns():
    z = _zones([100.0, 100.0], supply_kl=150.0)
    rec, info = redistribute(z, supply_ml=0.15)
    assert {"recommended_supply_kl", "recommended_unmet_kl",
            "recommended_shortage_risk"} <= set(rec.columns)
    assert info["requires_human_approval"] is True
