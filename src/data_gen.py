"""Synthetic multi-city hourly water-consumption generator (vectorised).

Mirrors the structure of the Kaggle DM1718 "Water Consumption" dataset and the
Smart Cities Open Data Portal city datasets: hourly consumption per zone (DMA),
plus weather, reservoir and economic covariates.

Signal model per zone:
    demand = base(pop, lpcd, zone_share)
             * daily_curve(hour)          # twin peaks: morning + evening
             * weekly_curve(dayofweek)
             * seasonal(month)            # summer spike, monsoon dip
             * weather(temp, rain)
             * (1 + noise)
    plus injected anomalies (leaks / burst pipes / tanker failure).

Zones are generated together per city with NumPy broadcasting, so the whole of
India (580+ cities, 2600+ zones) generates in seconds rather than minutes.
"""
import numpy as np
import pandas as pd

from city_registry import all_cities

CLIMATE_TEMP_OFFSET = {
    "arid": 6.0, "semi-arid": 4.0, "tropical-dry": 4.5, "tropical-wet": 2.0,
    "coastal": 1.5, "humid-subtropical": 2.5, "temperate-highland": -6.0,
}

_HOUR_CURVE = np.array([
    0.45, 0.35, 0.30, 0.30, 0.40, 0.70, 1.15, 1.55, 1.60, 1.35, 1.15, 1.05,
    1.00, 0.95, 0.95, 1.00, 1.15, 1.40, 1.60, 1.55, 1.30, 1.05, 0.80, 0.60,
])
_DAY_CURVE = np.array([1.00, 1.05, 1.03, 1.02, 1.04, 1.12, 1.15])
_MONTH_CURVE = np.array([
    1.05, 1.08, 1.15, 1.25, 1.35, 1.20, 1.00, 0.95, 1.00, 1.05, 1.00, 1.02,
])

COLUMNS = [
    "timestamp", "city", "state_ut", "zone_id", "zone_index", "climate_zone",
    "pop_millions", "growth_rate", "lpcd_norm", "lat", "lon", "demand_kl",
    "temp_c", "rain_mm", "reservoir_pct", "tariff_inr_per_kwh",
    "pump_energy_kwh", "treatment_inr_per_kl",
]


def _season_temp(month, climate, base_temp=28.0):
    offset = CLIMATE_TEMP_OFFSET.get(climate, 2.0)
    seasonal = 8.0 * np.sin((month - 4) / 12.0 * 2 * np.pi)
    return base_temp + offset + seasonal


def generate_city_hourly(city, hours=24 * 30, seed=0, anomaly_rate=0.004):
    """Return a DataFrame of hourly demand (kL) for every zone of one city."""
    rng = np.random.default_rng(seed)
    nz = int(city["n_zones"])
    pop = city["pop_millions"] * 1_000_000
    lpcd = city["lpcd_norm"]

    shares = rng.lognormal(0.0, 0.5, size=nz)
    shares = shares / shares.sum()

    ts = pd.date_range(pd.Timestamp("2024-03-01 00:00:00"), periods=hours, freq="h")
    month = ts.month.to_numpy()
    hour = ts.hour.to_numpy()
    dow = ts.dayofweek.to_numpy()
    n = len(ts)

    temp = _season_temp(month, city["climate_zone"]) + rng.normal(0, 2.0, n)
    wet = city["climate_zone"] in ("tropical-wet", "coastal", "humid-subtropical")
    rain_prob = 0.35 if wet else 0.10
    is_monsoon = (month >= 6) & (month <= 9)
    rain = np.where(is_monsoon, rng.random(n) < rain_prob, rng.random(n) < 0.03)
    rain_mm = rain * rng.gamma(2.0, 6.0, size=n)

    base_res = city.get("reservoir_baseline_pct", 60.0)
    res_season = 8.0 * np.sin((month - 6) / 12.0 * 2 * np.pi)
    reservoir = np.clip(base_res + res_season + np.cumsum(rng.normal(0, 0.05, n)), 15, 98)
    tariff = np.where((hour >= 18) & (hour < 22), 8.40, 6.20).astype(float)
    tariff[int(n * 0.5):] += 0.30
    treatment = np.full(n, 14.50)
    treatment[int(n * 0.5):] += 1.10

    # per-zone base demand (kL/h) and the shared time-varying shape
    city_daily_kl = pop * lpcd / 1000.0
    zone_base = (city_daily_kl * shares / 24.0)[:, None]                 # (nz,1)
    shape = (_HOUR_CURVE[hour] * _DAY_CURVE[dow] * _MONTH_CURVE[month - 1]
             * (1.0 + 0.02 * (temp - 28.0))
             * (1.0 - 0.05 * rain_mm / 20.0))[None, :]                  # (1,n)
    demand = zone_base * shape * (1.0 + rng.normal(0, 0.06, (nz, n)))
    demand = np.clip(demand, 0.05, None)
    n_anom = int(n * anomaly_rate)
    if n_anom:
        for z in range(nz):
            idx = rng.choice(n, size=n_anom, replace=False)
            demand[z, idx] *= rng.uniform(2.0, 4.5, size=n_anom)

    pump_energy = np.clip(demand * 0.28 + rng.normal(0, 0.2, (nz, n)), 0, None)

    ang = 2 * np.pi * np.arange(nz) / max(nz, 1)
    zlat = city["lat"] + 0.03 * np.cos(ang)
    zlon = city["lon"] + 0.03 * np.sin(ang)

    df = pd.DataFrame({
        "timestamp": np.tile(ts.to_numpy(), nz),
        "city": city["city"],
        "state_ut": city["state_ut"],
        "zone_id": [f"{city['city'][:3].upper()}-Z{z+1:02d}" for z in range(nz)
                    for _ in range(n)],
        "zone_index": np.repeat(np.arange(nz), n),
        "climate_zone": city["climate_zone"],
        "pop_millions": city["pop_millions"],
        "growth_rate": city.get("growth_rate", 0.0),
        "lpcd_norm": lpcd,
        "lat": np.repeat(zlat, n),
        "lon": np.repeat(zlon, n),
        "demand_kl": demand.ravel().round(3),
        "temp_c": np.tile(temp, nz).round(2),
        "rain_mm": np.tile(rain_mm, nz).round(2),
        "reservoir_pct": np.tile(reservoir, nz).round(2),
        "tariff_inr_per_kwh": np.tile(tariff, nz).round(2),
        "pump_energy_kwh": pump_energy.ravel().round(3),
        "treatment_inr_per_kl": np.tile(treatment, nz).round(2),
    })
    return df[COLUMNS]


def generate_all(cities=None, hours=24 * 30, seed=42):
    cities = cities or all_cities()
    frames = [generate_city_hourly(c, hours=hours, seed=seed + i)
              for i, c in enumerate(cities)]
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    df = generate_all(hours=24 * 30)
    print(df.shape)
    print(df.head())
