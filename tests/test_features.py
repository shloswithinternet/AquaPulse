"""Feature engineering: leakage guards and schema."""
import pytest

from features import FEATURES, build_features
from models.demand_forecast import evaluate


def test_features_do_not_include_target():
    assert "demand_kl" not in FEATURES


def test_lags_use_only_the_past(raw):
    f = build_features(raw[raw["city"] == "Mumbai"])
    f = f.sort_values(["zone_id", "timestamp"]).reset_index(drop=True)
    for z, g in f.groupby("zone_id"):
        g = g.reset_index(drop=True)
        assert g["lag_1"].iloc[5] == pytest.approx(g["demand_kl"].iloc[4])
        exp = g["demand_kl"].iloc[1:25].mean()
        assert g["roll_24_mean"].iloc[25] == pytest.approx(exp, rel=1e-6)


def test_new_factor_features_present():
    for c in ("reservoir_pct", "tariff_inr_per_kwh", "energy_per_kl", "growth_rate"):
        assert c in FEATURES


def test_evaluate_returns_expected_metrics(feat):
    y = feat["demand_kl"].to_numpy(float)
    m = evaluate(y, feat["pred_demand"].to_numpy(float))
    assert set(m) == {"MAE", "RMSE", "MAPE_%", "R2"}
    assert m["MAE"] >= 0
