"""Shortage / excess supply-chain consistency."""
import numpy as np
import pandas as pd

from models.shortage import (city_shortage_flags, compute_shortage,
                             supply_chain_summary, zone_demand_summary)


def _zones(demand, supply_each):
    return pd.DataFrame({
        "city": ["X"] * len(demand), "state_ut": ["S"] * len(demand),
        "zone_id": [f"Z{i}" for i in range(len(demand))],
        "lat": [0.0] * len(demand), "lon": [0.0] * len(demand),
        "pred_daily_kl": demand, "pred_peak_kl": np.array(demand) / 24,
        "obs_daily_kl": demand,
    })


def test_shortage_and_excess_are_complementary():
    z = _zones([100, 100, 100], None)
    z = compute_shortage(z, supply_ml=0.2, allocation_kl=[150.0, 100.0, 50.0])
    # zone 0 over-served -> excess 50, zone 2 under-served -> shortage 50
    assert z.loc[0, "excess_kl"] == 50.0 and z.loc[0, "shortage_kl"] == 0.0
    assert z.loc[2, "shortage_kl"] == 50.0 and z.loc[2, "excess_kl"] == 0.0
    # balance = supply - demand must equal excess - shortage
    for i in range(3):
        assert abs(z.loc[i, "balance_kl"] -
                   (z.loc[i, "excess_kl"] - z.loc[i, "shortage_kl"])) < 1e-9


def test_zero_demand_no_shortage():
    z = _zones([0.0, 0.0], None)
    z = compute_shortage(z, supply_ml=0.1, allocation_kl=[0.0, 0.0])
    assert (z["shortage_kl"] == 0).all()
    assert (z["shortage_risk"] == 0).all()


def test_chain_summary_consistency():
    z = _zones([100, 100, 100], None)
    z = compute_shortage(z, supply_ml=0.2, allocation_kl=[150.0, 100.0, 50.0])
    z = city_shortage_flags(z)
    s = supply_chain_summary(z)
    assert s["total_shortage_kl"] == 50.0
    assert s["total_excess_kl"] == 50.0
    assert s["zones_in_shortage"] == 1 and s["zones_in_excess"] == 1


def test_zone_demand_summary_from_features(feat):
    z = zone_demand_summary(feat[feat["city"] == "Mumbai"])
    assert {"pred_daily_kl", "pred_peak_kl", "zone_id"} <= set(z.columns)
    assert (z["pred_daily_kl"] > 0).all()
