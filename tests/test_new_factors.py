"""Crisis, storage, essential-services, urbanization and nearest-donor tests."""
import numpy as np
import pandas as pd

from models import crisis, essential, storage, urbanization
from models.divergence import bearing, nearest_donors
from models.redistribution import optimise_allocation


def _city(pop=2.0, zone="A", g=0.02):
    return {"city": zone, "pop_millions": pop, "growth_rate": g,
            "reservoir_baseline_pct": 60.0, "n_zones": 4}


def _zones(n=4):
    return [{"zone_id": f"Z{i}", "pred_daily_kl": 1000.0 - i * 100,
             "pred_peak_kl": 50.0, "obs_daily_kl": 990.0} for i in range(n)]


# ---------------- crisis ----------------
def test_crisis_levels_and_range():
    short = {"total_demand_kl": 1000.0, "total_shortage_kl": 900.0, "worst_zone_risk": 0.9}
    ab = {"balance_ratio": -0.5}
    dis = {"disaster_risk": 0.8}
    st = {"reservoir_stress": 0.7}
    pop = {"annual_growth_rate": 0.03}
    c = crisis.analyse(_city(), short, ab, dis, st, [{}] * 20, pop)
    assert 0.0 <= c["score"] <= 1.0
    assert c["level"] in ("stable", "watch", "warning", "emergency")
    assert c["level"] in ("warning", "emergency")
    assert any(p["action"] for p in c["plan"])


def test_crisis_stable_when_nothing_wrong():
    c = crisis.analyse(_city(), {"total_demand_kl": 1000.0, "total_shortage_kl": 0.0,
                                 "worst_zone_risk": 0.0}, {"balance_ratio": 0.3},
                       {"disaster_risk": 0.05}, {"reservoir_stress": 0.0}, [],
                       {"annual_growth_rate": 0.0})
    assert c["level"] == "stable"
    assert c["score"] < 0.25


def test_crisis_links_anomalies_to_plan():
    c = crisis.analyse(_city(), {"total_demand_kl": 1000.0, "total_shortage_kl": 100.0,
                                 "worst_zone_risk": 0.1}, {"balance_ratio": 0.0},
                       {"disaster_risk": 0.1}, {"reservoir_stress": 0.0}, [{}] * 20,
                       {"annual_growth_rate": 0.0})
    assert any("abnormal" in p["action"].lower() for p in c["plan"])


# ---------------- storage ----------------
def test_storage_buffer_and_posture():
    s = storage.analyse(_city(), reservoir_pct=40.0, supply_ml=100.0, demand_kl=50000.0)
    assert s["days_of_buffer"] > 0
    assert s["posture"] == "conserve"          # 40% is below the 60% baseline
    assert s["reserve_gap_kl"] >= 0


def test_storage_release_when_full():
    s = storage.analyse(_city(), reservoir_pct=95.0, supply_ml=100.0, demand_kl=1000.0)
    assert s["releasable_kl"] > 0
    assert s["posture"] == "release"


# ---------------- essential services ----------------
def test_essential_facilities_and_floor():
    e = essential.analyse(_city(pop=5.0), _zones(6), total_demand_kl=10000.0)
    assert e["facilities"]["hospitals"] >= 1
    assert e["protection_floor_kl"] > 0
    assert len(e["essential_zones"]) >= 1
    assert len(e["essential_zones"]) <= len(_zones(6))


def test_essential_zones_are_the_largest():
    e = essential.analyse(_city(pop=1.0), _zones(4), 4000.0)
    assert "Z0" in e["essential_zones"]        # Z0 has the highest demand


# ---------------- urbanization ----------------
def test_urbanization_projection_monotonic():
    u = urbanization.analyse(_city(pop=4.0, g=0.03), demand_kl=10000.0)
    pops = [p["urban_pop_millions"] for p in u["projection"]]
    assert pops == sorted(pops)
    assert u["land_converted_km2_10y"] >= 0
    assert u["extra_demand_kl_10y"] >= 0
    assert 0.30 <= u["urban_share"] <= 0.94


def test_urbanization_declining_city():
    u = urbanization.analyse(_city(pop=0.05, g=-0.01), demand_kl=1000.0)
    assert u["projection"][-1]["urban_pop_millions"] <= u["projection"][0]["urban_pop_millions"]


# ---------------- nearest donors ----------------
def test_nearest_donors_sorted_and_filtered():
    me = {"city": "Pune", "lat": 18.52, "lon": 73.86}
    cands = [{"city": "Pune", "lat": 18.52, "lon": 73.86, "excess_kl": 999, "band": "x"},
             {"city": "Mumbai", "lat": 19.08, "lon": 72.88, "excess_kl": 50000, "band": "severe-abundance"},
             {"city": "Surat", "lat": 21.17, "lon": 72.83, "excess_kl": 80000, "band": "abundance"},
             {"city": "Dry", "lat": 18.0, "lon": 73.0, "excess_kl": 0, "band": "scarcity"}]
    nd = nearest_donors(me, cands, k=3)
    assert [d["city"] for d in nd] == ["Mumbai", "Surat"]      # self + zero-surplus excluded
    assert nd[0]["distance_km"] < nd[1]["distance_km"]         # nearest first
    assert nd[0]["direction"] in ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def test_bearing_compass():
    assert bearing(0, 0, 1, 0) == "N"
    assert bearing(0, 0, 0, 1) == "E"
    assert bearing(1, 0, 0, 0) == "S"


# ---------------- essential-constrained optimiser ----------------
def test_optimiser_enforces_essential_floor():
    d = np.array([100.0, 100.0, 100.0])
    alloc, unmet, _, status = optimise_allocation(
        d, 200.0, essential_fraction=0.70, essential_zones={0})
    assert status == "optimal"
    assert alloc[0] >= 70.0 - 1e-6              # essential zone protected
    assert alloc.sum() <= 200.0 + 1e-6


def test_optimiser_reports_essential_infeasibility():
    d = np.array([100.0, 100.0, 100.0])
    _, _, _, status = optimise_allocation(d, 10.0, essential_fraction=0.9,
                                          essential_zones={0, 1, 2})
    assert "infeasible-essential" in status
