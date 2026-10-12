"""AquaPulse API.

    uvicorn api:app --reload --port 8000

Serves the dashboard and exposes the factors, the divergence engine, what-if
scenarios, live weather, and the Water Assistant (/ask).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import RESULTS_DIR                       # noqa: E402
import assistant                                     # noqa: E402
import economics                                     # noqa: E402
import weather                                       # noqa: E402
from city_registry import get_city                   # noqa: E402
from models import divergence                          # noqa: E402
from models.redistribution import redistribute       # noqa: E402
from models.shortage import compute_shortage, city_shortage_flags, supply_chain_summary  # noqa: E402

app = FastAPI(title="AquaPulse — Smart Water Redistribution", version="2.0")

_BUNDLE: dict | None = None


def bundle() -> dict:
    global _BUNDLE
    if _BUNDLE is None:
        p = RESULTS_DIR / "bundle.json"
        if not p.exists():
            raise HTTPException(503, "Run `python src/pipeline.py` first to build results/bundle.json.")
        _BUNDLE = json.loads(p.read_text(encoding="utf-8"))
    return _BUNDLE


class Scenario(BaseModel):
    supply_ml: float | None = None
    demand_multiplier: float = 1.0
    hazard: str | None = None          # drought|heatwave|flood|cyclone|quake
    population_years: int = 0
    mode: str = "shortage"


class Ask(BaseModel):
    question: str


class Compare(BaseModel):
    historical_date: str | None = None
    future_date: str | None = None


class EconUpdate(BaseModel):
    name: str
    value: float
    source: str = "manual entry"


@app.get("/", response_class=HTMLResponse)
def index():
    p = RESULTS_DIR / "dashboard.html"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return "<h3>Run <code>python src/pipeline.py</code> first to build the dashboard.</h3>"


@app.get("/national")
def national():
    return bundle()["national"]


@app.get("/metrics")
def metrics():
    return bundle()["metrics"]


@app.get("/cities")
def cities():
    return [{"city": c["city"], "state_ut": c["state_ut"], "climate_zone": c["climate_zone"],
             "abundance_band": c["abundance"]["band"],
             "worst_zone_risk": c["shortage"]["worst_zone_risk"]} for c in bundle()["cities"]]


def _city(city: str) -> dict:
    c = next((x for x in bundle()["cities"] if x["city"].lower() == city.lower()), None)
    if not c:
        raise HTTPException(404, f"Unknown or non-demo city: {city}")
    return c


@app.get("/city/{city}")
def city_detail(city: str):
    return _city(city)


@app.get("/weather/{city}")
def city_weather(city: str):
    meta = get_city(city)
    if not meta:
        raise HTTPException(404, f"Unknown city: {city}")
    return weather.get_weather(meta)


@app.post("/scenario/{city}")
def scenario(city: str, s: Scenario):
    """Recompute shortage, excess, divergence and the plan under an override.

    The historical bundle is never mutated; results are labelled SIMULATED.
    """
    c = _city(city)
    meta = get_city(city)
    supply_ml = s.supply_ml if s.supply_ml is not None else c["supply_ml"]

    zones = np.array([z["pred_daily_kl"] for z in c["zones"]], dtype=float) * s.demand_multiplier
    # population adjustment
    if s.population_years > 0:
        g = meta["growth_rate"]
        zones = zones * ((1.0 + g) ** s.population_years)
    # disaster override
    if s.hazard:
        from config import DISASTER_EFFECT
        if s.hazard not in DISASTER_EFFECT:
            raise HTTPException(400, f"Unknown hazard: {s.hazard}")
        eff = DISASTER_EFFECT[s.hazard]
        zones = zones * eff["demand"]
        supply_ml = supply_ml * eff["supply"]

    zdf = c["zones"]
    import pandas as pd
    frame = pd.DataFrame([{"city": city, "state_ut": c["state_ut"], "zone_id": z["zone_id"],
                           "lat": z["lat"], "lon": z["lon"], "pred_daily_kl": d,
                           "pred_peak_kl": z["pred_peak_kl"], "obs_daily_kl": z["obs_daily_kl"]}
                          for z, d in zip(zdf, zones)])
    frame = compute_shortage(frame, supply_ml)          # proportional baseline
    frame = city_shortage_flags(frame)
    rec, info = redistribute(frame, supply_ml, mode=s.mode)
    div = divergence.route_within_city(frame)
    return JSONResponse({
        "scenario": True, "label": "SIMULATED — not an observation",
        "city": city, "supply_ml": supply_ml, "demand_multiplier": s.demand_multiplier,
        "hazard": s.hazard, "population_years": s.population_years,
        "shortage": supply_chain_summary(frame), "plan": info, "divergence": div,
    })


@app.get("/crisis/{city}")
def city_crisis(city: str):
    c = _city(city)
    return {"city": c["city"], "crisis": c["crisis"], "storage": c["storage"],
            "essential": c["essential"]}


@app.get("/donors/{city}")
def city_donors(city: str):
    c = _city(city)
    return {"city": c["city"], "residual_shortage_kl": c.get("residual_shortage_kl", 0.0),
            "nearest_donors": c.get("nearest_donors", []),
            "within_city": c["divergence"]}


@app.post("/compare/{city}")
def city_compare(city: str, body: Compare):
    """Compare a historical day with a forecast day for one city."""
    c = _city(city)
    H, F = c["history_daily"], c["forecast_daily"]
    h = next((x for x in H if x["date"] == body.historical_date), H[-1] if H else None)
    f = next((x for x in F if x["date"] == body.future_date), F[-1] if F else None)
    if not h or not f:
        raise HTTPException(404, "No such historical/forecast date for this city.")
    change = (100.0 * (f["forecast_kl"] - h["observed_kl"]) / h["observed_kl"]
              if h["observed_kl"] else None)
    return {"city": c["city"], "historical": h, "future": f,
            "demand_change_pct": None if change is None else round(change, 1)}


@app.post("/ask")
def ask(body: Ask):
    return assistant.answer(body.question, bundle())


@app.post("/economics")
def update_economics(u: EconUpdate):
    if u.value < 0:
        raise HTTPException(400, "Value must be non-negative.")
    try:
        saved = economics.save_override(u.name, u.value, u.source, kind="manual")
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"status": "ok", "name": u.name, "saved": saved,
            "note": "Re-run the pipeline to fold this into the bundle."}
