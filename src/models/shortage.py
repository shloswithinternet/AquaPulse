"""Shortage AND excess prediction — the two halves of the supply chain.

For every zone we compute:

    shortage_kl = max(0, demand - supply)      # the deficit
    excess_kl   = max(0, supply - demand)      # the surplus
    balance_kl  = supply - demand              # signed

so the dashboard can show, side by side, *who is short* and *who has spare* —
the two ends of the supply chain that the divergence engine then connects.
"""
from __future__ import annotations

import numpy as np

from config import EXCESS_THRESHOLD, SHORTAGE_RISK_THRESHOLD


def zone_demand_summary(df, target="demand_kl", pred_col="pred_demand",
                        horizon_hours=24):
    """Peak predicted demand and daily demand per zone (last `horizon_hours`)."""
    tail = df.sort_values("timestamp").groupby(["city", "zone_id"]).tail(horizon_hours)
    agg = (tail.groupby(["city", "state_ut", "zone_id", "lat", "lon"])
              .agg(pred_daily_kl=(pred_col, "sum"),
                   pred_peak_kl=(pred_col, "max"),
                   obs_daily_kl=(target, "sum"))
              .reset_index())
    return agg


def compute_shortage(zones, supply_ml, allocation_kl=None):
    """Compare demand with supply; add shortage, excess, balance and risk.

    If `allocation_kl` is None, supply is split proportional to demand (the
    do-nothing baseline). Returns the frame with all derived columns.
    """
    z = zones.copy()
    supply_kl = supply_ml * 1000.0
    if allocation_kl is None:
        share = z["pred_daily_kl"] / z["pred_daily_kl"].sum()
        z["supply_kl"] = supply_kl * share
    else:
        z["supply_kl"] = np.asarray(allocation_kl, dtype=float)

    z["balance_kl"] = z["supply_kl"] - z["pred_daily_kl"]
    z["shortage_kl"] = np.clip(z["pred_daily_kl"] - z["supply_kl"], 0, None)
    z["excess_kl"] = np.clip(z["supply_kl"] - z["pred_daily_kl"], 0, None)
    z["shortage_risk"] = np.where(z["pred_daily_kl"] > 0,
                                  z["shortage_kl"] / z["pred_daily_kl"], 0.0)
    z["excess_ratio"] = np.where(z["pred_daily_kl"] > 0,
                                 z["excess_kl"] / z["pred_daily_kl"], 0.0)
    z["supply_met_%"] = np.where(z["pred_daily_kl"] > 0,
                                 100.0 * (1 - z["shortage_risk"]), 100.0)
    return z


def city_shortage_flags(z, threshold=SHORTAGE_RISK_THRESHOLD):
    z = z.copy()
    z["at_risk"] = z["shortage_risk"] > threshold
    z["has_surplus"] = z["excess_ratio"] > EXCESS_THRESHOLD
    return z


def supply_chain_summary(z) -> dict:
    """Totals for the shortage side and the excess side of one city."""
    return {
        "total_demand_kl": round(float(z["pred_daily_kl"].sum()), 1),
        "total_supply_kl": round(float(z["supply_kl"].sum()), 1),
        "total_shortage_kl": round(float(z["shortage_kl"].sum()), 1),
        "total_excess_kl": round(float(z["excess_kl"].sum()), 1),
        "zones_in_shortage": int((z["shortage_kl"] > 0).sum()),
        "zones_in_excess": int((z["excess_kl"] > 0).sum()),
        "worst_zone_risk": round(float(z["shortage_risk"].max()), 4),
        "mean_risk": round(float(z["shortage_risk"].mean()), 4),
    }
