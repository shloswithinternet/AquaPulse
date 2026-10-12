"""Abundance / scarcity engine.

Answers: *is this city (or zone) water-rich or water-poor right now, and why?*

It starts from the physical water balance

    balance = effective_supply - adjusted_demand
    ratio   = balance / adjusted_demand

and then adjusts BOTH sides by the factors the project is required to consider:

    supply side : weather (rainfall / recharge), reservoir level, disaster risk
    demand side : weather (heat), population growth/decay, disaster risk

Every adjustment is returned explicitly as a "driver", so the dashboard can show
*why* a city is abundant or scarce instead of just a number.
"""
from __future__ import annotations

import math
from typing import Any

from config import ABUNDANCE_BANDS, KL_PER_ML


def classify(ratio: float) -> str:
    for lo, hi, label in ABUNDANCE_BANDS:
        if lo <= ratio < hi:
            return label
    return "balanced"


def abundance_index(ratio: float) -> float:
    """Map the balance ratio to a 0-100 index (50 = balanced)."""
    return round(50.0 + 50.0 * math.tanh(ratio / 0.60), 1)


def _weather_supply_factor(rain_mm: float, climate: str) -> tuple[float, str]:
    """Rainfall recharges local supply; dry spells reduce it. Bounded, modest."""
    wet_climates = {"tropical-wet", "coastal", "humid-subtropical"}
    wetness = 1.0 if climate in wet_climates else 0.7
    dry_term = math.tanh((6.0 - rain_mm) / 6.0) if rain_mm < 6 else 0.0
    f = 1.0 + 0.06 * wetness * math.tanh(rain_mm / 12.0) - 0.04 * wetness * dry_term
    return round(min(max(f, 0.92), 1.08), 4), f"rainfall {rain_mm:.1f} mm"


def _weather_demand_factor(temp_c: float) -> tuple[float, str]:
    """Heat raises demand above ~28 C, cool weather lowers it slightly."""
    f = 1.0 + 0.020 * max(temp_c - 28.0, 0.0) - 0.004 * max(24.0 - temp_c, 0.0)
    return round(min(max(f, 0.9), 1.6), 4), f"temperature {temp_c:.1f} C"


def _reservoir_factor(level_pct: float, baseline_pct: float) -> tuple[float, str]:
    """Storage above/below the city's normal level scales deliverable supply."""
    delta = (level_pct - baseline_pct) / 100.0
    f = 1.0 + 0.6 * delta
    return round(min(max(f, 0.85), 1.15), 4), f"reservoir {level_pct:.0f}% vs {baseline_pct:.0f}%"


def analyse(city: dict, demand_kl: float, supply_ml: float, *,
            rain_mm: float = 0.0, temp_c: float = 28.0, reservoir_pct: float | None = None,
            disaster: dict | None = None, population: dict | None = None,
            econ: dict | None = None) -> dict[str, Any]:
    """Full abundance/scarcity view for a city (or a zone, using zone demand)."""
    reservoir_pct = city.get("reservoir_baseline_pct", 60.0) if reservoir_pct is None else reservoir_pct
    base_supply_kl = supply_ml * KL_PER_ML

    drivers: list[dict[str, Any]] = []

    wsf, wsn = _weather_supply_factor(rain_mm, city.get("climate_zone", "semi-arid"))
    rsf, rsn = _reservoir_factor(reservoir_pct, city.get("reservoir_baseline_pct", 60.0))
    dsf = disaster["expected_supply_multiplier"] if disaster else 1.0
    supply_factor = wsf * rsf * dsf
    effective_supply = base_supply_kl * supply_factor
    drivers.append({"side": "supply", "factor": "weather/rainfall", "multiplier": wsf, "note": wsn})
    drivers.append({"side": "supply", "factor": "reservoir level", "multiplier": rsf, "note": rsn})
    if disaster:
        drivers.append({"side": "supply", "factor": f"disaster ({disaster['dominant_hazard']})",
                        "multiplier": dsf, "note": f"risk {disaster['disaster_risk']:.2f}"})

    wdf, wdn = _weather_demand_factor(temp_c)
    popf = population.get("ten_year_demand_factor", 1.0) if population else 1.0
    # Use a 1-year population factor for the "now" view (10-year shown separately).
    popf_now = next((p["demand_factor"] for p in population.get("projection", []) if p["years_ahead"] == 1), 1.0) if population else 1.0
    ddf = disaster["expected_demand_multiplier"] if disaster else 1.0
    demand_factor = wdf * popf_now * ddf
    adjusted_demand = demand_kl * demand_factor
    drivers.append({"side": "demand", "factor": "weather/heat", "multiplier": wdf, "note": wdn})
    if population:
        drivers.append({"side": "demand", "factor": "population (1 yr)", "multiplier": popf_now,
                        "note": f"{population['annual_growth_pct']:+.1f}%/yr, {population['trend']}"})
    if disaster:
        drivers.append({"side": "demand", "factor": f"disaster ({disaster['dominant_hazard']})",
                        "multiplier": ddf, "note": "hazard raises demand"})

    balance = effective_supply - adjusted_demand
    ratio = balance / adjusted_demand if adjusted_demand > 0 else 0.0
    band = classify(ratio)

    # economic stress: cost per kL vs a reference, adds context (not a water amount)
    econ_note = None
    if econ:
        by = econ["by_name"]
        cpk = (by["treatment_cost_inr_per_kl"]["value"] +
               by["energy_intensity_kwh_per_kl"]["value"] * by["electricity_tariff_inr_per_kwh"]["value"])
        econ_note = f"operating cost ~INR {cpk:.2f}/kL"

    return {
        "city": city["city"],
        "base_supply_kl": round(base_supply_kl, 1),
        "effective_supply_kl": round(effective_supply, 1),
        "base_demand_kl": round(demand_kl, 1),
        "adjusted_demand_kl": round(adjusted_demand, 1),
        "balance_kl": round(balance, 1),
        "balance_ratio": round(ratio, 4),
        "abundance_index": abundance_index(ratio),
        "band": band,
        "supply_factor": round(supply_factor, 4),
        "demand_factor": round(demand_factor, 4),
        "drivers": drivers,
        "economic_note": econ_note,
        "ten_year_demand_factor": round(popf, 4),
    }
