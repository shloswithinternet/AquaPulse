"""Natural-disaster factor.

Cities face different hazards (drought, heatwave, flood, cyclone, earthquake).
Each hazard moves BOTH the supply available and the demand required. This module
turns a city's hazard profile (from its climate zone) plus the season into an
expected supply/demand effect and a single 0-1 risk score.

Everything here is a transparent, rule-based model — not a live warning feed.
"""
from __future__ import annotations

from typing import Any

from config import DISASTER_EFFECT

# Seasonal weighting: month (1-12) -> per-hazard multiplier.
# Monsoon (Jun-Sep) raises flood/cyclone; pre-monsoon (Apr-Jun) raises heat/drought.
_SEASON = {
    "drought":  {1: 0.8, 2: 0.9, 3: 1.1, 4: 1.3, 5: 1.4, 6: 1.0, 7: 0.7, 8: 0.7, 9: 0.8, 10: 1.0, 11: 1.1, 12: 0.9},
    "heatwave": {1: 0.3, 2: 0.5, 3: 0.9, 4: 1.4, 5: 1.6, 6: 1.3, 7: 0.8, 8: 0.7, 9: 0.8, 10: 0.9, 11: 0.5, 12: 0.3},
    "flood":    {1: 0.3, 2: 0.3, 3: 0.4, 4: 0.5, 5: 0.7, 6: 1.4, 7: 1.7, 8: 1.7, 9: 1.4, 10: 0.9, 11: 0.5, 12: 0.3},
    "cyclone":  {1: 0.5, 2: 0.4, 3: 0.4, 4: 0.6, 5: 0.9, 6: 1.1, 7: 1.2, 8: 1.3, 9: 1.4, 10: 1.5, 11: 1.3, 12: 0.8},
    "quake":    {m: 1.0 for m in range(1, 13)},   # no strong seasonality
}


def hazard_scores(city: dict, month: int) -> dict[str, float]:
    """Season-adjusted relative likelihood per hazard (normalised to sum 1)."""
    profile = city["disaster_profile"]
    raw = {h: profile.get(h, 0.0) * _SEASON.get(h, {}).get(month, 1.0) for h in DISASTER_EFFECT}
    total = sum(raw.values()) or 1.0
    return {h: round(v / total, 4) for h, v in raw.items()}


def expected_effects(scores: dict[str, float]) -> dict[str, float]:
    """Probability-weighted supply and demand multipliers, blended with the
    (much more likely) 'no disaster' case."""
    from config import DISASTER_ANNUAL_PROBABILITY as P
    raw_s = sum(scores[h] * DISASTER_EFFECT[h]["supply"] for h in scores)
    raw_d = sum(scores[h] * DISASTER_EFFECT[h]["demand"] for h in scores)
    supply = (1.0 - P) * 1.0 + P * raw_s
    demand = (1.0 - P) * 1.0 + P * raw_d
    return {"supply_multiplier": round(supply, 4), "demand_multiplier": round(demand, 4)}


def risk_score(scores: dict[str, float]) -> float:
    """0-1 composite: how much this city's hazard mix is expected to hurt.

    Weighted by the *impact* of each hazard (how far its multipliers move away
    from 1.0), so a likely-but-mild hazard scores lower than a likely-severe one.
    """
    impact = sum(scores[h] * (abs(1 - DISASTER_EFFECT[h]["supply"]) +
                              abs(1 - DISASTER_EFFECT[h]["demand"])) for h in scores)
    return round(min(impact / 0.6, 1.0), 4)


def analyse(city: dict, month: int | None = None) -> dict[str, Any]:
    import datetime as _dt
    month = month or _dt.date.today().month
    scores = hazard_scores(city, month)
    effects = expected_effects(scores)
    top = max(scores, key=scores.get)
    return {
        "month": month,
        "hazard_likelihood": scores,
        "dominant_hazard": top,
        "expected_supply_multiplier": effects["supply_multiplier"],
        "expected_demand_multiplier": effects["demand_multiplier"],
        "disaster_risk": risk_score(scores),
        "note": ("Rule-based hazard model from climate zone + season. It is a "
                 "planning factor, NOT a live disaster warning."),
    }
