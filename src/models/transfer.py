"""Cross-city transfer: run one model on any Indian city, trained or not.

Three modes, in order of how much local data a city has:

1. zero-shot   -- the global model, trained on other cities, predicts a city it
                  has never seen, using only that city's meta-features.
2. few-shot    -- with N days of local history, fine-tune by re-fitting the
                  global model with local samples up-weighted.
3. donor-pick  -- when a city has no history at all, choose the k most similar
                  source cities (nearest in meta-feature space) and blend them.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from features import FEATURES
from models.demand_forecast import GlobalDemandModel, evaluate


META_COLS = ["log_pop", "lpcd_norm", "lat", "temp_c", "rain_mm"] + \
            [c for c in FEATURES if c.startswith("cz_")]

# The transfer report trains two extra models; cap rows/iterations so the whole
# pipeline stays interactive without changing what the experiment demonstrates.
TRANSFER_MAX_ROWS = 60000
TRANSFER_MAX_ITER = 180


def _subsample(X, y, max_rows, seed=0):
    if len(X) <= max_rows:
        return X, y
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(X), size=max_rows, replace=False)
    return X[idx], y[idx]


def _fit_fast(X, y):
    X, y = _subsample(X, y, TRANSFER_MAX_ROWS)
    return GlobalDemandModel(max_iter=TRANSFER_MAX_ITER).fit(X, y)


def _city_meta_vector(df):
    return df.groupby("city")[META_COLS].mean()


class TransferEngine:
    def __init__(self, source_cities):
        self.source_cities = list(source_cities)
        self.scaler = StandardScaler()
        self.model = None

    def fit_global(self, feat_df):
        X = feat_df[FEATURES].to_numpy(float)
        y = feat_df["demand_kl"].to_numpy(float)
        self.model = _fit_fast(X, y)
        self.scaler.fit(_city_meta_vector(feat_df).to_numpy())
        return self

    def nearest_donors(self, feat_df, target_city, k=3):
        meta = _city_meta_vector(feat_df)
        if target_city not in meta.index:
            return []
        Z = self.scaler.transform(meta.to_numpy())
        t = self.scaler.transform(meta.loc[[target_city]].to_numpy())[0]
        dist = np.linalg.norm(Z - t, axis=1)
        order = np.argsort(dist)
        return [(meta.index[i], round(float(dist[i]), 3))
                for i in order if meta.index[i] != target_city][:k]

    def zero_shot_eval(self, feat_df, target_city):
        """Train on all cities except target; test on target."""
        train = feat_df[feat_df["city"] != target_city]
        test = feat_df[feat_df["city"] == target_city]
        if test.empty:
            return None
        m = _fit_fast(train[FEATURES].to_numpy(float), train["demand_kl"].to_numpy(float))
        pred = m.predict(test[FEATURES].to_numpy(float))
        return evaluate(test["demand_kl"].to_numpy(float), pred)

    def few_shot_eval(self, feat_df, target_city, n_days=7):
        """Global model + up-weighted local window vs zero-shot."""
        train = feat_df[feat_df["city"] != target_city]
        local = feat_df[feat_df["city"] == target_city]
        if local.empty:
            return None
        cut = local["timestamp"].min() + pd.Timedelta(days=n_days)
        warm, test = local[local["timestamp"] < cut], local[local["timestamp"] >= cut]
        if len(warm) < 50 or len(test) < 50:
            return None
        combo = pd.concat([train, warm, warm, warm, warm, warm])  # ~5x weight on local
        m = _fit_fast(combo[FEATURES].to_numpy(float), combo["demand_kl"].to_numpy(float))
        pred = m.predict(test[FEATURES].to_numpy(float))
        return evaluate(test["demand_kl"].to_numpy(float), pred)
