"""
Feature engineering shared by every model.

The same feature vector is built for a Mumbai zone and a Surat zone, so a single
global model can learn across cities. City identity is expressed through
*normalised meta-features* (population, per-capita norm, climate one-hot,
latitude) rather than a raw city id -- that is what lets the model generalise to
a city it never trained on.
"""
import numpy as np
import pandas as pd

CLIMATE_ZONES = ["arid", "semi-arid", "tropical-dry", "tropical-wet",
                 "coastal", "humid-subtropical", "temperate-highland"]

FEATURES = (
    ["hour", "dow", "month", "is_weekend", "temp_c", "rain_mm",
     "reservoir_pct", "tariff_inr_per_kwh", "energy_per_kl", "growth_rate",
     "lag_1", "lag_24", "lag_168", "roll_24_mean", "roll_24_std",
     "log_pop", "lpcd_norm", "lat"]
    + [f"cz_{z}" for z in CLIMATE_ZONES]
)
TARGET = "demand_kl"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["city", "zone_id", "timestamp"]).copy()
    df["hour"] = df["timestamp"].dt.hour
    df["dow"] = df["timestamp"].dt.dayofweek
    df["month"] = df["timestamp"].dt.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)

    g = df.groupby(["city", "zone_id"])[TARGET]
    df["lag_1"] = g.shift(1)
    df["lag_24"] = g.shift(24)
    df["lag_168"] = g.shift(168)
    df["roll_24_mean"] = g.transform(lambda s: s.shift(1).rolling(24).mean())
    df["roll_24_std"] = g.transform(lambda s: s.shift(1).rolling(24).std())

    df["log_pop"] = np.log1p(df["pop_millions"])
    # energy used per kilolitre delivered (economic + operational signal)
    if "pump_energy_kwh" in df.columns:
        df["energy_per_kl"] = df["pump_energy_kwh"] / df[TARGET].clip(lower=1e-6)
    else:
        df["energy_per_kl"] = 0.0
    for z in CLIMATE_ZONES:
        df[f"cz_{z}"] = (df["climate_zone"] == z).astype(int)

    df = df.dropna(subset=["lag_168", "roll_24_mean", "roll_24_std"]).reset_index(drop=True)
    return df


def feature_matrix(df: pd.DataFrame):
    return df[FEATURES].to_numpy(dtype=float), df[TARGET].to_numpy(dtype=float)
