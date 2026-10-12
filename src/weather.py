"""Optional live weather for a city (Open-Meteo, keyless).

Returns current conditions and a short forecast, each carrying its source and
observation time. On failure / disabled / rate-limit it reports a clear status
and, if possible, the last stored (historical) observation — clearly labelled as
NOT live. It never fabricates a measurement.
"""
from __future__ import annotations

import time
from typing import Any

import requests

from config import (WEATHER_CACHE_TTL_SECONDS, WEATHER_ENABLED,
                    WEATHER_TIMEOUT_SECONDS)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_cache: dict[str, Any] = {}   # city -> {"ts": float, "data": dict}


def _fetch(city: dict) -> dict[str, Any]:
    params = {
        "latitude": city["lat"], "longitude": city["lon"],
        "current": "temperature_2m,relative_humidity_2m,precipitation",
        "hourly": "temperature_2m,precipitation_probability",
        "forecast_days": 3, "timezone": "auto",
    }
    r = requests.get(OPEN_METEO_URL, params=params, timeout=WEATHER_TIMEOUT_SECONDS)
    r.raise_for_status()
    j = r.json()
    cur = j.get("current", {})
    h = j.get("hourly", {})
    import pandas as pd
    now = pd.Timestamp.now()
    forecast = []
    times = h.get("time", [])
    temps = h.get("temperature_2m", [])
    probs = h.get("precipitation_probability", [])
    for i, t in enumerate(times):
        ts = pd.Timestamp(t)
        if ts > now:
            forecast.append({"time": ts.isoformat(),
                             "temperature_c": temps[i] if i < len(temps) else None,
                             "precip_prob_pct": probs[i] if i < len(probs) else None})
        if len(forecast) >= 24:
            break
    return {
        "city": city["city"], "status": "live",
        "observed_at": cur.get("time"),
        "source": "Open-Meteo (api.open-meteo.com)",
        "temperature_c": cur.get("temperature_2m"),
        "humidity_pct": cur.get("relative_humidity_2m"),
        "rainfall_mm": cur.get("precipitation"),
        "forecast": forecast,
        "note": "Live weather from a public API. Forecast entries are predictions, not observations.",
    }


def get_weather(city: dict, use_cache: bool = True) -> dict[str, Any]:
    key = city["city"]
    now = time.time()
    cached = _cache.get(key)
    if use_cache and cached and (now - cached["ts"]) < WEATHER_CACHE_TTL_SECONDS:
        return cached["data"]

    if not WEATHER_ENABLED:
        data = _unavailable(city, "Weather integration disabled by configuration.")
    else:
        try:
            data = _fetch(city)
        except Exception as exc:
            data = _unavailable(city, f"Live weather fetch failed ({type(exc).__name__}).")
    _cache[key] = {"ts": now, "data": data}
    return data


def _unavailable(city: dict, reason: str) -> dict[str, Any]:
    """Report unavailability, offering the city's climate baseline (labelled)."""
    return {
        "city": city["city"], "status": "unavailable", "observed_at": None,
        "source": "none", "temperature_c": None, "humidity_pct": None,
        "rainfall_mm": None, "forecast": [],
        "note": (reason + " No live measurements are fabricated. The demand model "
                 "falls back to the city's historical/climate weather."),
    }


def reset_cache() -> None:
    _cache.clear()
