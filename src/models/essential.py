"""Essential-services protection.

Hospitals, emergency services and other critical facilities must get water before
anyone else. This module estimates how many such facilities a city has, the share
of demand they represent, the protection floor the optimiser must guarantee, and
which zones hold them.

Facility counts are illustrative (scaled from population), and the share of
demand they consume is a stated assumption — the point is that the optimiser is
given a hard floor it cannot violate for those zones.
"""
from __future__ import annotations

from typing import Any


def analyse(city: dict, zones: list[dict], total_demand_kl: float) -> dict[str, Any]:
    pop = float(city["pop_millions"])
    hospitals = max(1, round(pop * 12))
    emergency = max(1, round(pop * 8))          # fire, police, disaster response
    critical = max(1, round(pop * 6))           # govt, water treatment, power, transit

    essential_share = 0.18 if pop >= 2 else (0.15 if pop >= 0.3 else 0.12)
    essential_demand = total_demand_kl * essential_share
    protection_floor = essential_demand         # must be met in full

    # zones holding the critical facilities = the largest zones by demand
    ordered = sorted(zones, key=lambda z: -z["pred_daily_kl"])
    k = max(1, round(len(ordered) * 0.25))
    essential_zones = ordered[:k]
    protected = [{
        "zone_id": z["zone_id"],
        "demand_kl": round(z["pred_daily_kl"], 1),
        "floor_kl": round(z["pred_daily_kl"] * essential_share, 1),
    } for z in essential_zones]

    return {
        "facilities": {"hospitals": hospitals, "emergency": emergency, "critical": critical,
                       "total": hospitals + emergency + critical},
        "essential_share": essential_share,
        "essential_demand_kl": round(essential_demand, 1),
        "protection_floor_kl": round(protection_floor, 1),
        "essential_zones": [z["zone_id"] for z in essential_zones],
        "protected": protected,
        "note": ("Facility counts are illustrative, scaled from population. The protection "
                 "floor is enforced as a hard constraint in the optimiser."),
    }
