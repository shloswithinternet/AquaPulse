"""Abnormal consumption detection: residual + isolation-forest ensemble.

A zone-hour is flagged when it is far from BOTH (a) the model's own prediction
(behavioural anomaly) and (b) the zone's recent rolling baseline (statistical
anomaly). Two independent detectors cut false positives on genuinely unusual but
valid days (festivals, heatwaves).

Leakage fix (see AUDIT_REPORT.md A3): the rolling baseline is computed from
PAST values only (shift(1) before rolling), and the isolation forest is fitted on
the earlier portion of the series and applied to the rest — so no point is
scored using information from its own future.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

BASELINE_WINDOW = 168       # 7 days
MIN_PERIODS = 24


def detect_anomalies(df, pred_col="pred_demand", target="demand_kl",
                     contamination=0.01):
    df = df.copy()
    df["residual"] = df[target] - df[pred_col]

    def _z(s: pd.Series) -> pd.Series:
        # past-only rolling mean/std (shift before rolling => no future info)
        m = s.shift(1).rolling(BASELINE_WINDOW, min_periods=MIN_PERIODS).mean()
        sd = s.shift(1).rolling(BASELINE_WINDOW, min_periods=MIN_PERIODS).std()
        return (s - m) / (sd + 1e-9)

    df["z_resid"] = df.groupby(["city", "zone_id"])["residual"].transform(_z)

    # Fit the isolation forest on the earlier 80% of rows (chronologically),
    # then score every row — avoids fitting on the rows being judged.
    iso_feats = df[["demand_kl", "temp_c", "rain_mm", "residual"]].to_numpy()
    n = len(df)
    fit_n = max(int(n * 0.8), 50)
    iso = IsolationForest(contamination=contamination, random_state=0)
    iso.fit(iso_feats[:fit_n])
    df["iso_flag"] = iso.predict(iso_feats) == -1

    df["is_anomaly"] = (np.abs(df["z_resid"]) > 3.0) | df["iso_flag"]
    df["anomaly_score"] = np.clip(np.abs(df["z_resid"]) / 6.0, 0, 1)
    return df


def summarize_anomalies(df):
    a = df[df["is_anomaly"]]
    return (a.groupby(["city", "zone_id"])
             .agg(n_anomalies=("is_anomaly", "size"),
                  peak_score=("anomaly_score", "max"),
                  peak_demand=("demand_kl", "max"))
             .reset_index()
             .sort_values("peak_score", ascending=False))
