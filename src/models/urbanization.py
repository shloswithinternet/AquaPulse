"""Urbanization projection.

Cities grow outward: rural and forest land on the fringe becomes built-up, and
the people who move in consume more water than they did in the countryside. This
module projects that change — urban population, built-up area, the land converted
from rural/forest use, and the extra water demand it implies.

Model (simple and stated):
    urban_share    = f(population)                       # larger = more urbanised
    builtup_km2    = urban_population / urban_density    # density held constant
    growth(t)      = (1 + g)^t                           # from the city's growth rate
    extra demand(t)= demand * ((1+g)^t - 1)

Illustrative, not a land-use survey — but it is the number that matters for
planning: how much MORE water the fringe will draw.
"""
from __future__ import annotations

import math
from typing import Any

URBAN_DENSITY_PER_KM2 = 12000.0     # people per km2 of built-up area (illustrative)
YEARS = [0, 5, 10, 20]


def urban_share(pop_millions: float) -> float:
    s = 0.30 + 0.12 * math.log10(max(pop_millions * 1000.0, 1.0))
    return round(min(max(s, 0.30), 0.94), 3)


def analyse(city: dict, demand_kl: float) -> dict[str, Any]:
    pop = float(city["pop_millions"])
    g = float(city.get("growth_rate", 0.0))
    share = urban_share(pop)
    urban_pop = pop * share
    builtup_now = urban_pop * 1e6 / URBAN_DENSITY_PER_KM2

    projection = []
    for t in YEARS:
        up = urban_pop * (1.0 + g) ** t
        projection.append({
            "years_ahead": t,
            "urban_pop_millions": round(up, 3),
            "builtup_km2": round(up * 1e6 / URBAN_DENSITY_PER_KM2, 1),
            "demand_factor": round((1.0 + g) ** t, 4),
            "extra_demand_kl": round(demand_kl * ((1.0 + g) ** t - 1.0), 1),
        })

    ten = projection[2]
    conversion_km2 = round(ten["builtup_km2"] - builtup_now, 1)
    return {
        "urban_share": share,
        "urban_pop_millions": round(urban_pop, 3),
        "builtup_km2_now": round(builtup_now, 1),
        "builtup_km2_10y": ten["builtup_km2"],
        "land_converted_km2_10y": max(conversion_km2, 0.0),
        "extra_demand_kl_10y": ten["extra_demand_kl"],
        "extra_demand_kl_20y": projection[3]["extra_demand_kl"],
        "projection": projection,
        "density_assumption": URBAN_DENSITY_PER_KM2,
        "note": ("Illustrative projection. New built-up area appears on the urban fringe, "
                 "converting rural and forest land; the extra demand is what planning must "
                 "reserve water for."),
    }
