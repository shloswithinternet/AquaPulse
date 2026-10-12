"""Economic-factor monitoring.

Tracks the economic inputs that decide whether water is *affordable to move*:
electricity tariff, pumping energy, treatment cost, fuel. Every value carries
value / unit / source / effective-date / last-updated / kind so the UI can be
honest about what is measured, estimated, manual or illustrative.

Cost maths is deliberately simple and unit-safe:
    energy_cost  = energy_kwh * tariff_inr_per_kwh
    treatment    = volume_kl * treatment_inr_per_kl
    total_cost   = energy_cost + treatment
Cost per kL is only computed for a stated period so hourly rates never get
divided by monthly volumes.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from config import (DEFAULT_FUEL_INR_PER_LITRE, DEFAULT_TARIFF_INR_PER_KWH,
                    DEFAULT_TREATMENT_INR_PER_KL, ENERGY_INTENSITY_KWH_PER_KL,
                    RESULTS_DIR)

# Operator overrides are persisted here (simple JSON store, easy to inspect).
OVERRIDE_FILE = RESULTS_DIR / "economic_overrides.json"

VARIABLE_DEFS = [
    {"name": "electricity_tariff_inr_per_kwh", "label": "Electricity tariff",
     "unit": "INR/kWh", "default": DEFAULT_TARIFF_INR_PER_KWH},
    {"name": "treatment_cost_inr_per_kl", "label": "Water treatment cost",
     "unit": "INR/kL", "default": DEFAULT_TREATMENT_INR_PER_KL},
    {"name": "energy_intensity_kwh_per_kl", "label": "Pumping energy intensity",
     "unit": "kWh/kL", "default": ENERGY_INTENSITY_KWH_PER_KL},
    {"name": "fuel_cost_inr_per_litre", "label": "Fuel cost (diesel)",
     "unit": "INR/litre", "default": DEFAULT_FUEL_INR_PER_LITRE},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_overrides() -> dict[str, dict]:
    if OVERRIDE_FILE.exists():
        try:
            return json.loads(OVERRIDE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_override(name: str, value: float, source: str, kind: str = "manual",
                  effective_date: str | None = None, notes: str = "") -> dict:
    data = load_overrides()
    data[name] = {
        "value": float(value), "source": source,
        "effective_date": effective_date or datetime.now().date().isoformat(),
        "last_updated": _now_iso(), "kind": kind, "notes": notes,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    OVERRIDE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data[name]


def get_state() -> dict[str, Any]:
    """Current economic picture, with provenance for every value."""
    overrides = load_overrides()
    now = datetime.now(timezone.utc)
    variables = []
    for v in VARIABLE_DEFS:
        name = v["name"]
        entry = {"name": name, "label": v["label"], "unit": v["unit"]}
        if name in overrides:
            o = overrides[name]
            entry.update(value=o["value"], source=o["source"],
                         effective_date=o["effective_date"],
                         last_updated=o["last_updated"], kind=o["kind"])
        else:
            entry.update(value=v["default"],
                         source="Illustrative default (config.py)",
                         effective_date=None, last_updated=None, kind="illustrative")
        stale = False
        if entry.get("last_updated"):
            try:
                age = (now - datetime.fromisoformat(entry["last_updated"])).total_seconds() / 3600
                entry["age_hours"] = round(age, 1)
                stale = age > 24 * 30
            except Exception:
                pass
        entry["stale"] = stale
        variables.append(entry)
    return {
        "variables": variables,
        "by_name": {v["name"]: v for v in variables},
        "note": ("Illustrative values by default. Only a value whose source says so "
                 "may be treated as live. Operator entries are labelled 'manual'."),
    }


def energy_cost_inr(energy_kwh: float, tariff_inr_per_kwh: float) -> float:
    if energy_kwh < 0 or tariff_inr_per_kwh < 0:
        raise ValueError("Energy and tariff must be non-negative.")
    return energy_kwh * tariff_inr_per_kwh


def operating_cost_per_kl(tariff_inr_per_kwh: float, treatment_inr_per_kl: float,
                          energy_intensity_kwh_per_kl: float) -> float:
    """Cost to deliver one kilolitre: treatment + pumping energy."""
    return treatment_inr_per_kl + energy_intensity_kwh_per_kl * tariff_inr_per_kwh


def estimate_operating_cost(volume_kl: float, econ: dict) -> dict[str, Any]:
    by = econ["by_name"]
    tariff = by["electricity_tariff_inr_per_kwh"]["value"]
    treatment = by["treatment_cost_inr_per_kl"]["value"]
    ei = by["energy_intensity_kwh_per_kl"]["value"]
    energy_kwh = volume_kl * ei
    energy_cost = energy_cost_inr(energy_kwh, tariff)
    treatment_cost = volume_kl * treatment
    return {
        "volume_kl": round(volume_kl, 1),
        "period": "day",
        "energy_kwh": round(energy_kwh, 1),
        "energy_cost_inr": round(energy_cost, 2),
        "treatment_cost_inr": round(treatment_cost, 2),
        "total_operating_cost_inr": round(energy_cost + treatment_cost, 2),
        "cost_per_kl_inr": round(operating_cost_per_kl(tariff, treatment, ei), 3),
        "is_estimate": True,
        "caveat": "Estimate from an illustrative tariff/intensity, not a metered bill.",
    }
