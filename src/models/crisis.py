"""Water-crisis prediction and emergency plan.

Combines every stress signal the system computes into one 0-1 crisis score with
a level (stable / watch / warning / emergency), lists the drivers that pushed it
up, and proposes an ordered emergency plan. It also links abnormal consumption
into the plan, because an unexplained surge is itself a crisis trigger.

Everything here is a transparent weighted model over already-computed signals —
no hidden inputs, and no claim to be an official warning.
"""
from __future__ import annotations

from typing import Any

LEVELS = [(0.25, "stable"), (0.45, "watch"), (0.65, "warning"), (1.01, "emergency")]


def _level(score: float) -> str:
    for thr, name in LEVELS:
        if score < thr:
            return name
    return "emergency"


def analyse(city: dict, shortage: dict, abundance: dict, disaster: dict,
            storage: dict, anomalies: list, population: dict) -> dict[str, Any]:
    demand = max(shortage.get("total_demand_kl", 0.0), 1.0)
    shortage_pressure = min(1.0, shortage.get("total_shortage_kl", 0.0) / demand)
    worst_risk = min(1.0, shortage.get("worst_zone_risk", 0.0))
    disaster_risk = float(disaster.get("disaster_risk", 0.0))
    res_stress = storage.get("reservoir_stress", 0.0)
    anom_pressure = min(1.0, len(anomalies) / 12.0)
    growth = float(population.get("annual_growth_rate", 0.0))
    pop_pressure = min(1.0, max(0.0, growth) / 0.03)
    dry_stress = max(0.0, -float(abundance.get("balance_ratio", 0.0)))

    drivers = [
        {"factor": "shortage pressure", "value": round(shortage_pressure, 3), "weight": 0.34},
        {"factor": "worst-zone risk", "value": round(worst_risk, 3), "weight": 0.16},
        {"factor": "disaster risk", "value": round(disaster_risk, 3), "weight": 0.14},
        {"factor": "reservoir stress", "value": round(res_stress, 3), "weight": 0.14},
        {"factor": "abnormal consumption", "value": round(anom_pressure, 3), "weight": 0.10},
        {"factor": "population pressure", "value": round(pop_pressure, 3), "weight": 0.06},
        {"factor": "dry-spell stress", "value": round(min(dry_stress, 1.0), 3), "weight": 0.06},
    ]
    score = round(sum(d["value"] * d["weight"] for d in drivers), 4)
    level = _level(score)
    top = sorted(drivers, key=lambda d: -d["value"] * d["weight"])[:3]

    plan: list[dict[str, Any]] = []
    if level in ("warning", "emergency"):
        plan.append({"priority": 1, "action": "Protect essential services",
                     "detail": "Guarantee the lifeline allocation to hospitals, emergency "
                               "services and critical facilities before any other release."})
        plan.append({"priority": 2, "action": "Draw on the nearest abundant city",
                     "detail": "Activate the divergence transfer from the closest city with a "
                               "water surplus (see the Divergence page)."})
        plan.append({"priority": 3, "action": "Release reserve storage",
                     "detail": "Release the reservoir volume held above the reserve target."})
    if level == "watch":
        plan.append({"priority": 1, "action": "Tighten non-essential use",
                     "detail": "Restrict irrigation, construction and municipal non-drinking use."})
        plan.append({"priority": 2, "action": "Pre-position reserves",
                     "detail": "Hold storage at or above the reserve target for the coming week."})
    if anom_pressure >= 0.34:
        plan.append({"priority": 1 if level in ("warning", "emergency") else 2,
                     "action": "Investigate the abnormal-consumption zones",
                     "detail": "Unexplained surges in flagged zones should be checked for a "
                               "burst or unauthorised draw; divert water away from confirmed "
                               "wastage toward at-risk zones."})
    if level == "stable":
        plan.append({"priority": 3, "action": "Maintain watch",
                     "detail": "No action required; keep monitoring weather and storage."})

    return {
        "score": score,
        "level": level,
        "drivers": drivers,
        "top_drivers": top,
        "horizon_days": 7,
        "plan": plan,
        "note": ("Weighted model over the system's own signals — a planning aid, "
                 "not an official warning."),
    }
