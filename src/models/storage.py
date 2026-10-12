"""Water storage and future allotment.

Turns the reservoir level into an actual storage volume, computes how many days
of demand it represents, and decides how much to HOLD for a future crisis versus
how much can be RELEASED now. It also computes the volume that must be reserved
to cover essential services for the coming week.

Illustrative capacity: a city's reservoir system is assumed to hold about 45
days of its effective supply. That factor is documented here, not hidden.
"""
from __future__ import annotations

from typing import Any

STORAGE_DAYS_CAPACITY = 45.0     # reservoir volume expressed in days of supply
RESERVE_TARGET_DAYS = 21.0       # keep at least this many days in hand
ESSENTIAL_COVER_DAYS = 7.0       # reserve enough for essential services for a week


def analyse(city: dict, reservoir_pct: float, supply_ml: float, demand_kl: float,
            essential_share: float = 0.15) -> dict[str, Any]:
    baseline = float(city.get("reservoir_baseline_pct", 60.0))
    capacity_kl = max(supply_ml * 1000.0 * STORAGE_DAYS_CAPACITY, 1.0)
    stored_kl = capacity_kl * reservoir_pct / 100.0
    demand = max(demand_kl, 1.0)

    days_buffer = stored_kl / demand
    reserve_target = demand * RESERVE_TARGET_DAYS
    essential_reserve = demand * essential_share * ESSENTIAL_COVER_DAYS

    # release only what sits above the reserve target (and never below it)
    releasable = max(0.0, stored_kl - reserve_target)
    # if we are below target, say how much must be rebuilt
    reserve_gap = max(0.0, reserve_target - stored_kl)
    reservoir_stress = max(0.0, min(1.0, (baseline - reservoir_pct) / max(baseline, 1.0)))

    if reservoir_pct < baseline - 5:
        posture = "conserve"
        advice = ("Storage is below normal: hold the reserve, restrict non-essential use, "
                  "and rebuild the buffer before the next dry spell.")
    elif releasable > demand * 3:
        posture = "release"
        advice = ("Storage is comfortable: surplus above the reserve target can be released "
                  "to the zones that need it now.")
    else:
        posture = "hold"
        advice = "Storage is near the reserve target: hold it and monitor."

    return {
        "reservoir_pct": round(reservoir_pct, 1),
        "baseline_pct": baseline,
        "capacity_kl": round(capacity_kl, 1),
        "stored_kl": round(stored_kl, 1),
        "days_of_buffer": round(days_buffer, 1),
        "reserve_target_kl": round(reserve_target, 1),
        "reserve_gap_kl": round(reserve_gap, 1),
        "releasable_kl": round(releasable, 1),
        "essential_reserve_kl": round(essential_reserve, 1),
        "reservoir_stress": round(reservoir_stress, 4),
        "posture": posture,
        "advice": advice,
        "capacity_days_assumption": STORAGE_DAYS_CAPACITY,
        "reserve_target_days": RESERVE_TARGET_DAYS,
        "note": "Storage capacity is illustrative (a stated number of days of supply).",
    }
