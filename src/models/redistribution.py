"""Supply redistribution: linear-programming allocation across zones.

Two modes:

* **shortage** — minimise priority-weighted unmet demand (service-first);
* **cost-aware** — minimise  sum(w_i * unmet_i) + lambda * operating_cost.

Constraints:
    alloc_i + unmet_i >= demand_i              (meet demand as far as possible)
    sum(alloc_i)      <= supply_kl             (cannot use more than you have)
    min_ratio*d_i     <= alloc_i <= max_ratio*d_i
    alloc_i >= essential_fraction * d_i        (for essential-service zones —
                                                hospitals, emergency, critical)

Essential zones are guaranteed their protection floor before anything else, so
the optimiser can never buy cost savings by starving a hospital.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linprog


def optimise_allocation(pred_demand_kl, supply_kl, max_ratio=1.15, min_ratio=0.60,
                        priority=None, mode="shortage", cost_per_kl=None,
                        lambda_cost=0.0, essential_fraction=0.0,
                        essential_zones=None):
    """Return (allocation_kl, unmet_kl, total_unmet, status)."""
    d = np.asarray(pred_demand_kl, dtype=float)
    n = len(d)
    priority = np.ones(n) if priority is None else np.asarray(priority, float)
    essential_zones = essential_zones or set()

    c = np.concatenate([np.zeros(n), priority])
    if mode == "cost":
        cost = np.zeros(n) if cost_per_kl is None else np.asarray(cost_per_kl, float)
        if cost.max() > 0:
            cost = cost / cost.max()
        c = np.concatenate([lambda_cost * cost, priority])

    A_ub = np.hstack([-np.eye(n), -np.eye(n)])
    b_ub = -d
    A_sup = np.concatenate([np.ones(n), np.zeros(n)]).reshape(1, -1)
    A_ub = np.vstack([A_ub, A_sup])
    b_ub = np.concatenate([b_ub, np.array([supply_kl])])

    # essential-service floor: alloc_i >= essential_fraction * d_i
    ess_idx = [i for i in range(n) if i in essential_zones] if essential_zones else []
    if essential_fraction > 0 and ess_idx:
        for i in ess_idx:
            row = np.zeros(2 * n)
            row[i] = -1.0
            A_ub = np.vstack([A_ub, row])
            b_ub = np.concatenate([b_ub, np.array([-essential_fraction * d[i]])])
        # infeasible if the essential floor cannot be met from the supply
        need = sum(essential_fraction * d[i] for i in ess_idx)
        if need > supply_kl + 1e-9:
            alloc = supply_kl * d / (d.sum() + 1e-9)
            alloc = np.minimum(alloc, max_ratio * d)
            unmet = np.clip(d - alloc, 0, None)
            return alloc, unmet, float(unmet.sum()), \
                f"infeasible-essential (floor {need:.0f} kL > supply {supply_kl:.0f} kL)"

    lb = min_ratio * d.copy()
    for i in ess_idx:                      # never below the essential floor
        lb[i] = max(lb[i], essential_fraction * d[i])
    ub = np.concatenate([max_ratio * d, d])
    bounds = list(zip(np.concatenate([lb, np.zeros(n)]), ub))

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    if not res.success:
        alloc = supply_kl * d / (d.sum() + 1e-9)
        alloc = np.minimum(alloc, max_ratio * d)
        unmet = np.clip(d - alloc, 0, None)
        return alloc, unmet, float(unmet.sum()), "fallback:" + str(res.message)

    alloc = res.x[:n]
    unmet = np.clip(d - alloc, 0, None)
    return alloc, unmet, float(unmet.sum()), "optimal"


def redistribute(zones, supply_ml, priority_by_risk=True, mode="shortage",
                 cost_per_kl=None, lambda_cost=0.0,
                 essential_fraction=0.0, essential_zones=None):
    """Apply the LP to a zone frame; returns (frame, info)."""
    z = zones.copy().reset_index(drop=True)
    supply_kl = supply_ml * 1000.0
    prio = (0.5 + z["shortage_risk"].to_numpy()) if priority_by_risk else None
    # essential_zones arrives as zone ids; the optimiser works on positions
    ess_idx = set()
    if essential_zones and "zone_id" in z.columns:
        ids = list(z["zone_id"])
        ess_idx = {i for i, zid in enumerate(ids) if zid in essential_zones}
    alloc, unmet, total_unmet, status = optimise_allocation(
        z["pred_daily_kl"].to_numpy(), supply_kl, priority=prio,
        mode=mode, cost_per_kl=cost_per_kl, lambda_cost=lambda_cost,
        essential_fraction=essential_fraction, essential_zones=ess_idx)

    z["recommended_supply_kl"] = alloc
    z["recommended_unmet_kl"] = unmet
    z["recommended_excess_kl"] = np.clip(alloc - z["pred_daily_kl"], 0, None)
    z["recommended_shortage_risk"] = np.where(z["pred_daily_kl"] > 0,
                                              unmet / z["pred_daily_kl"], 0.0)
    return z, {"status": status, "total_unmet_kl": round(total_unmet, 1),
               "mode": mode, "lambda_cost": lambda_cost,
               "essential_fraction": essential_fraction,
               "n_essential_zones": len(ess_idx),
               "requires_human_approval": True}
