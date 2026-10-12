"""Population growth / decay factor.

Demand is not static: a growing city needs more water every year, a declining
one less. This module turns the illustrative annual growth rate carried by each
city into an explicit projection, so the forecast and the abundance index can be
adjusted for demographic change.

Model (deliberately simple and explainable):
    population(t) = population(0) * (1 + g) ** t          t in years
    demand_factor(t) = (1 + g) ** t                       (demand scales with pop)

`g` comes from city_registry.growth_rate(); it is an illustrative figure, not a
census projection, and every output is labelled as a projection.
"""
from __future__ import annotations

from typing import Any

YEARS_AHEAD = [0, 1, 3, 5, 10]


def classify_trend(g: float) -> str:
    if g >= 0.015:
        return "growing"
    if g >= 0.004:
        return "slow-growing"
    if g > -0.004:
        return "stable"
    return "declining"


def project_population(pop_millions: float, g: float, years: int) -> float:
    return round(pop_millions * (1.0 + g) ** years, 4)


def demand_factor(g: float, years: int) -> float:
    """Multiplier applied to a base demand to account for population change."""
    return round((1.0 + g) ** years, 4)


def analyse(city: dict) -> dict[str, Any]:
    """Full population-factor view for one city."""
    g = float(city["growth_rate"])
    pop = float(city["pop_millions"])
    projection = [
        {"years_ahead": t, "pop_millions": project_population(pop, g, t),
         "demand_factor": demand_factor(g, t)}
        for t in YEARS_AHEAD
    ]
    return {
        "annual_growth_rate": g,
        "annual_growth_pct": round(g * 100, 2),
        "trend": classify_trend(g),
        "current_pop_millions": pop,
        "projection": projection,
        "ten_year_pop_millions": project_population(pop, g, 10),
        "ten_year_demand_factor": demand_factor(g, 10),
        "note": ("Population growth/decay is an ILLUSTRATIVE model from city size "
                 "and climate, not a census projection. Demand is assumed to scale "
                 "with population."),
    }
