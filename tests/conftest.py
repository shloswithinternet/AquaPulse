"""Shared fixtures for the AquaPulse test-suite."""
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from city_registry import all_cities            # noqa: E402
from data_gen import generate_all               # noqa: E402
from features import build_features, FEATURES   # noqa: E402
from models.demand_forecast import GlobalDemandModel  # noqa: E402


@pytest.fixture(scope="session")
def demo_cities():
    want = ["Mumbai", "Ahmedabad", "Jaipur", "Kochi"]
    return [c for c in all_cities() if c["city"] in want]


@pytest.fixture(scope="session")
def raw(demo_cities):
    return generate_all(demo_cities, hours=24 * 12)      # 12 days, fast


@pytest.fixture(scope="session")
def feat(raw):
    f = build_features(raw)
    m = GlobalDemandModel(max_iter=80).fit(f[FEATURES].to_numpy(float),
                                           f["demand_kl"].to_numpy(float))
    f["pred_demand"] = m.predict(f[FEATURES].to_numpy(float))
    return f
