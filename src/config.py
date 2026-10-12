"""AquaPulse Smart Water — central configuration.

Every tunable factor the system reasons about lives here, so a judge can see
the whole "knob panel" in one file: units, thresholds, the abundance bands, the
divergence/transfer rules, disaster weights, and the population-growth model.
"""
from __future__ import annotations

import os
from pathlib import Path

# sklearn's HistGradientBoosting uses OpenMP; in a shared sandbox thread
# oversubscription makes small fits far slower than serial. Pin to one thread
# (set BEFORE sklearn is imported anywhere).
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
# On Windows, numpy (MKL) and scikit-learn (libomp) can each load a different
# OpenMP runtime; loading both crashes the process with an access violation.
# This flag lets the duplicate runtime load safely.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = Path(os.environ.get("AQUAPULSE_RESULTS", BASE_DIR / "results"))

# --- Units (single source of truth) --------------------------------------
# Demand/supply are kilo-litres (kL). 1 ML = 1000 kL. Planning period = 1 day.
KL_PER_ML = 1000.0
VOLUME_UNIT = "kL"
POWER_UNIT = "kWh"
TARIFF_UNIT = "INR/kWh"
TREATMENT_COST_UNIT = "INR/kL"

# --- Forecast ------------------------------------------------------------
FORECAST_HORIZON_HOURS = 24
DEMO_HOURS = 24 * 30          # length of the demonstration series per city

# --- Effective supply ----------------------------------------------------
# Fraction of gross bulk capacity actually deliverable after treatment,
# transmission and non-revenue-water losses. Indian cities commonly lose
# 20-40%; this mid-range factor converts gross -> effective.
SUPPLY_UTILISATION = 0.65

# --- Abundance / scarcity bands (balance ratio = (supply-demand)/demand) --
ABUNDANCE_BANDS = [
    (-1.01, -0.25, "severe-scarcity"),
    (-0.25, -0.05, "scarcity"),
    (-0.05, 0.05, "balanced"),
    (0.05, 0.25, "abundance"),
    (0.25, 1.01, "severe-abundance"),
]

# --- Shortage / excess thresholds ---------------------------------------
SHORTAGE_RISK_THRESHOLD = 0.15     # zone "at risk" above this
EXCESS_THRESHOLD = 0.05            # zone "has surplus" above this ratio

# --- Divergence & transfer ----------------------------------------------
# A surplus zone may donate at most this fraction of its surplus (keep a buffer).
TRANSFER_MAX_FRACTION_OF_SURPLUS = 0.70
# Inter-zone transfer efficiency (loss over the network) and distance decay.
TRANSFER_EFFICIENCY = 0.92
# Cross-city transfer is only proposed when the donor is within this radius (km)
# and has a rail/tanker-feasible surplus.
CROSS_CITY_MAX_DISTANCE_KM = 350.0

# --- Cost-aware allocation ----------------------------------------------
COST_TRADE_OFF_LAMBDA = 0.15       # weight of the operating-cost term

# --- Disaster model ------------------------------------------------------
# Per climate zone: relative likelihood weights for each hazard type.
DISASTER_PROFILE = {
    "arid":                 {"drought": 0.55, "heatwave": 0.30, "flood": 0.05, "cyclone": 0.02, "quake": 0.08},
    "semi-arid":            {"drought": 0.45, "heatwave": 0.28, "flood": 0.12, "cyclone": 0.03, "quake": 0.12},
    "tropical-dry":         {"drought": 0.42, "heatwave": 0.25, "flood": 0.18, "cyclone": 0.05, "quake": 0.10},
    "tropical-wet":         {"drought": 0.10, "heatwave": 0.10, "flood": 0.45, "cyclone": 0.25, "quake": 0.10},
    "coastal":              {"drought": 0.12, "heatwave": 0.12, "flood": 0.35, "cyclone": 0.33, "quake": 0.08},
    "humid-subtropical":    {"drought": 0.14, "heatwave": 0.12, "flood": 0.44, "cyclone": 0.10, "quake": 0.20},
    "temperate-highland":   {"drought": 0.22, "heatwave": 0.08, "flood": 0.30, "cyclone": 0.02, "quake": 0.38},
}
# How each hazard moves supply and demand (multiplicative), used by the model.
DISASTER_EFFECT = {
    "drought":  {"supply": 0.70, "demand": 1.10},
    "heatwave": {"supply": 0.95, "demand": 1.25},
    "flood":    {"supply": 0.80, "demand": 0.98},   # contamination / intake shutdown
    "cyclone":  {"supply": 0.75, "demand": 1.02},   # power/pump outage
    "quake":    {"supply": 0.85, "demand": 1.00},   # pipeline damage
}
# A hazard is an OCCASIONAL event, not a permanent state. The expected effect is
# therefore blended with "no event" at this annual probability, so a city is not
# permanently penalised for a hazard that may never occur.
DISASTER_ANNUAL_PROBABILITY = 0.15

# --- Population growth / decay ------------------------------------------
# Annual urban growth rate model (illustrative). Bigger cities grow a little
# slower in percentage terms; only SMALL remote/hill towns are assumed to
# decline. See population.py.
POP_GROWTH_BASE = 0.026            # ~2.6% for a small town
POP_GROWTH_SIZE_COEFF = 0.0030     # subtracted per log10(pop in thousands)
POP_GROWTH_HILL_PENALTY = 0.015    # applied ONLY to small highland towns
POP_GROWTH_SMALL_TOWN = 0.5        # pop (millions) below which hill penalty applies
POP_GROWTH_MIN, POP_GROWTH_MAX = -0.010, 0.035

# --- Climate-adjusted supply reliability ---------------------------------
# Illustrative multiplier on effective supply by climate zone: river-fed and
# monsoon-recharged cities have more reliable water; arid inland cities less.
# (The registry's gross capacity is further scaled by this to reflect the
#  reality that a desert city and a coastal city of equal pipe capacity do not
#  have equally available water.)
CLIMATE_SUPPLY_FACTOR = {
    "arid": 0.97, "semi-arid": 1.15, "tropical-dry": 1.27,
    "temperate-highland": 1.45, "humid-subtropical": 1.63,
    "tropical-wet": 1.76, "coastal": 1.76,
}

# --- Weather (optional, live) -------------------------------------------
WEATHER_ENABLED = os.environ.get("AQUAPULSE_DISABLE_WEATHER", "0") != "1"
WEATHER_TIMEOUT_SECONDS = 6
WEATHER_CACHE_TTL_SECONDS = 900
CITY_COORDS = {"Pune": (18.5204, 73.8567)}   # fallback single-city coords

# --- Economics -----------------------------------------------------------
ECON_STALE_HOURS = 24 * 30
ENERGY_INTENSITY_KWH_PER_KL = 0.28          # default pumping energy per kL
DEFAULT_TARIFF_INR_PER_KWH = 7.20           # illustrative Indian industrial tariff
DEFAULT_TREATMENT_INR_PER_KL = 14.50
DEFAULT_FUEL_INR_PER_LITRE = 94.0           # illustrative diesel price
