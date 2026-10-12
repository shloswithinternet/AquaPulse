"""Demand forecasting: one global gradient-boosted model across all cities."""
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class GlobalDemandModel:
    """A single model trained on many cities; predicts any city's next-hour demand.

    HistGradientBoosting handles the mixed numeric/categorical feature matrix
    well and trains in seconds, which keeps the whole pipeline interactive.
    """

    def __init__(self, **kw):
        params = dict(max_iter=300, learning_rate=0.06, max_depth=8,
                      l2_regularization=1.0, random_state=0)
        params.update(kw)
        self.model = HistGradientBoostingRegressor(**params)

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return np.clip(self.model.predict(X), 0.0, None)


def evaluate(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    # MAPE guarded against zeros
    denom = np.where(np.abs(y_true) < 1e-6, np.nan, y_true)
    mape = np.nanmean(np.abs((y_true - y_pred) / denom)) * 100
    r2 = r2_score(y_true, y_pred)
    mape_val = float(mape) if not np.isnan(mape) else 0.0
    r2_val = float(r2) if not np.isnan(r2) else 0.0
    return {"MAE": round(float(mae), 3), "RMSE": round(float(rmse), 3),
            "MAPE_%": round(mape_val, 2), "R2": round(r2_val, 4)}
