"""Water Assistant and API behaviour."""
import pytest

import assistant


def _city(name="Testville", band="balanced", idx=50.0):
    return {
        "city": name, "state_ut": "TestState", "lat": 19.0, "lon": 73.0,
        "climate_zone": "semi-arid", "pop_millions": 2.0, "supply_ml": 300.0,
        "gross_supply_ml": 460.0, "effective_supply_ml": 290.0, "n_zones": 2,
        "growth_rate": 0.018, "reservoir_baseline_pct": 55.0,
        "weather": {"status": "unavailable", "source": "none", "observed_at": None,
                    "temperature_c": None, "rainfall_mm": None, "humidity_pct": None,
                    "forecast": [], "note": "no live weather"},
        "disaster": {"month": 6, "dominant_hazard": "drought",
                     "hazard_likelihood": {"drought": 0.6, "heatwave": 0.2, "flood": 0.1,
                                           "cyclone": 0.05, "quake": 0.05},
                     "expected_supply_multiplier": 0.97, "expected_demand_multiplier": 1.02,
                     "disaster_risk": 0.4, "note": "rule-based"},
        "population": {"annual_growth_rate": 0.018, "annual_growth_pct": 1.8,
                       "trend": "growing", "current_pop_millions": 2.0,
                       "projection": [{"years_ahead": 0, "pop_millions": 2.0, "demand_factor": 1.0},
                                      {"years_ahead": 1, "pop_millions": 2.036, "demand_factor": 1.018},
                                      {"years_ahead": 3, "pop_millions": 2.11, "demand_factor": 1.055},
                                      {"years_ahead": 5, "pop_millions": 2.187, "demand_factor": 1.093},
                                      {"years_ahead": 10, "pop_millions": 2.392, "demand_factor": 1.196}],
                       "ten_year_pop_millions": 2.392, "ten_year_demand_factor": 1.196, "note": ""},
        "abundance": {"city": name, "base_supply_kl": 300000.0, "effective_supply_kl": 290000.0,
                      "base_demand_kl": 280000.0, "adjusted_demand_kl": 285000.0,
                      "balance_kl": 5000.0, "balance_ratio": 0.018, "abundance_index": idx,
                      "band": band, "supply_factor": 0.97, "demand_factor": 1.02,
                      "drivers": [{"side": "supply", "factor": "weather/rainfall", "multiplier": 0.98, "note": ""}],
                      "economic_note": None, "ten_year_demand_factor": 1.196},
        "shortage": {"total_demand_kl": 280000.0, "total_supply_kl": 285000.0,
                     "total_shortage_kl": 20000.0, "total_excess_kl": 25000.0,
                     "zones_in_shortage": 1, "zones_in_excess": 1,
                     "worst_zone_risk": 0.3, "mean_risk": 0.15},
        "divergence": {"scope": "within-city", "divergence_index": 0.12,
                       "total_shortage_kl": 20000.0, "total_excess_kl": 25000.0,
                       "transferable_excess_kl": 17500.0, "delivered_kl": 12000.0,
                       "residual_shortage_kl": 8000.0,
                       "transfers": [{"from_zone": "T-Z1", "to_zone": "T-Z2", "sent_kl": 13000.0,
                                      "delivered_kl": 12000.0, "loss_kl": 1000.0, "efficiency": 0.92}]},
        "operating_cost": {"total_operating_cost_inr": 500000.0, "cost_per_kl_inr": 16.5},
        "plan": {"mode": "shortage", "lp_status": "optimal", "baseline_unmet_kl": 20000.0,
                 "optimised_unmet_kl": 8000.0, "unmet_reduction_pct": 60.0,
                 "max_risk_before": 0.3, "max_risk_after": 0.12, "requires_human_approval": True},
        "plan_cost": {"mode": "cost", "lp_status": "optimal", "optimised_unmet_kl": 9000.0,
                      "cost_per_kl_inr": 16.5},
        "zones": [{"zone_id": "T-Z1", "lat": 19.0, "lon": 73.0, "pred_daily_kl": 150000.0,
                   "pred_peak_kl": 6250.0, "obs_daily_kl": 148000.0, "supply_kl": 175000.0,
                   "shortage_kl": 0.0, "excess_kl": 25000.0, "balance_kl": 25000.0,
                   "shortage_risk": 0.0, "at_risk": False, "has_surplus": True,
                   "abundance_band": "abundance", "recommended_supply_kl": 150000.0,
                   "recommended_unmet_kl": 0.0, "recommended_shortage_risk": 0.0},
                  {"zone_id": "T-Z2", "lat": 19.1, "lon": 73.1, "pred_daily_kl": 130000.0,
                   "pred_peak_kl": 5417.0, "obs_daily_kl": 129000.0, "supply_kl": 110000.0,
                   "shortage_kl": 20000.0, "excess_kl": 0.0, "balance_kl": -20000.0,
                   "shortage_risk": 0.3, "at_risk": True, "has_surplus": False,
                   "abundance_band": "scarcity", "recommended_supply_kl": 130000.0,
                   "recommended_unmet_kl": 0.0, "recommended_shortage_risk": 0.0}],
        "trend": [{"date": "2026-06-01", "observed": 270000.0, "predicted": 275000.0}],
        "crisis": {"score": 0.4, "level": "watch", "horizon_days": 7,
                   "drivers": [{"factor": "shortage pressure", "value": 0.2, "weight": 0.34}],
                   "top_drivers": [], "plan": [{"priority": 1, "action": "Tighten non-essential use",
                                                "detail": "restrict irrigation"}], "note": ""},
        "storage": {"reservoir_pct": 55.0, "baseline_pct": 55.0, "days_of_buffer": 20.0,
                    "posture": "hold", "releasable_kl": 1000.0, "reserve_gap_kl": 0.0,
                    "essential_reserve_kl": 100.0, "advice": "hold", "capacity_days_assumption": 45},
        "essential": {"facilities": {"hospitals": 24, "emergency": 16, "critical": 12, "total": 52},
                      "essential_share": 0.18, "essential_demand_kl": 1000.0,
                      "protection_floor_kl": 1000.0, "essential_zones": ["T-Z1"],
                      "protected": [], "note": ""},
        "urbanization": {"urban_share": 0.7, "builtup_km2_now": 100.0, "builtup_km2_10y": 130.0,
                         "land_converted_km2_10y": 30.0, "extra_demand_kl_10y": 5000.0,
                         "extra_demand_kl_20y": 11000.0, "density_assumption": 12000,
                         "projection": [{"years_ahead": 0, "urban_pop_millions": 1.4,
                                         "builtup_km2": 100.0, "demand_factor": 1.0,
                                         "extra_demand_kl": 0.0}], "note": ""},
        "population_water": {"pop_millions": 2.0, "demand_kl": 280000.0, "lpcd_now": 140.0,
                             "lpcd_norm": 135.0, "gap_lpcd": 5.0, "ratio_index": 103.7, "note": ""},
        "nearest_donors": [{"city": "Richville", "distance_km": 90.0, "direction": "N",
                            "band": "severe-abundance", "surplus_kl": 40000.0,
                            "deliverable_kl": 25000.0, "lat": 20.0, "lon": 73.0}],
        "residual_shortage_kl": 8000.0,
        "history_daily": [{"date": "2026-06-01", "observed_kl": 270000.0, "temp_c": 31.0,
                           "rain_mm": 0.0, "reservoir_pct": 55.0}],
        "forecast_daily": [{"date": "2026-06-02", "forecast_kl": 280000.0, "weekday_factor": 1.0}],
        "anomalies": [{"zone_id": "T-Z2", "time": "2026-06-01 05:00", "observed_kl": 900.0,
                       "expected_kl": 300.0, "z": 4.1, "score": 0.68, "direction": "up"}],
    }


@pytest.fixture
def mini_bundle():
    econ = {"variables": [{"name": "electricity_tariff_inr_per_kwh", "label": "Electricity tariff",
                           "unit": "INR/kWh", "value": 7.2, "kind": "illustrative"}],
            "by_name": {"electricity_tariff_inr_per_kwh": {"value": 7.2, "kind": "illustrative"},
                        "treatment_cost_inr_per_kl": {"value": 14.5, "kind": "illustrative"},
                        "energy_intensity_kwh_per_kl": {"value": 0.28, "kind": "illustrative"}},
            "note": ""}
    return {
        "meta": {"target_city": "Testville"},
        "metrics": {}, "economics": econ,
        "national": {"n_cities": 1, "n_zones": 2, "n_states_ut": 1, "total_demand_kl": 280000.0,
                     "total_supply_kl": 285000.0, "total_shortage_kl": 20000.0,
                     "total_excess_kl": 25000.0, "at_risk_zones": 1, "divergence_index": 0.12,
                     "cross_city_transfers": {"transfers": []}},
        "cities": [_city()],
    }


def test_assistant_answers_with_grounded_numbers(mini_bundle):
    out = assistant.answer("what is the shortage in Testville?", mini_bundle)
    assert out["intent"] == "shortage"
    assert "20,000" in out["answer"] or "20000" in out["answer"]


def test_assistant_handles_worst_city(mini_bundle):
    out = assistant.answer("which city is worst?", mini_bundle)
    assert out["intent"] == "worst" and "Testville" in out["answer"]


def test_assistant_help(mini_bundle):
    out = assistant.answer("what can you do?", mini_bundle)
    assert out["intent"] == "help"


def test_assistant_never_invents_weather(mini_bundle):
    out = assistant.answer("weather in Testville", mini_bundle)
    assert "unavailable" in out["answer"].lower() or "not" in out["answer"].lower()


def test_api_endpoints(monkeypatch, mini_bundle):
    import api
    monkeypatch.setattr(api, "bundle", lambda: mini_bundle)
    from fastapi.testclient import TestClient
    c = TestClient(api.app)

    assert c.get("/national").status_code == 200
    assert c.get("/cities").json()[0]["city"] == "Testville"
    assert c.get("/city/Testville").status_code == 200
    assert c.get("/city/Nowhere").status_code == 404
    r = c.post("/ask", json={"question": "shortage in Testville"})
    assert r.status_code == 200 and r.json()["intent"] == "shortage"


def test_api_scenario(monkeypatch, mini_bundle):
    import api
    monkeypatch.setattr(api, "bundle", lambda: mini_bundle)
    from fastapi.testclient import TestClient
    c = TestClient(api.app)
    r = c.post("/scenario/Testville", json={"supply_ml": 200.0, "demand_multiplier": 1.2})
    assert r.status_code == 200
    body = r.json()
    assert body["scenario"] is True
    assert "SIMULATED" in body["label"]


def test_api_scenario_bad_hazard(monkeypatch, mini_bundle):
    import api
    monkeypatch.setattr(api, "bundle", lambda: mini_bundle)
    from fastapi.testclient import TestClient
    c = TestClient(api.app)
    assert c.post("/scenario/Testville", json={"hazard": "meteor"}).status_code == 400


def test_api_crisis_and_donors(monkeypatch, mini_bundle):
    import api
    monkeypatch.setattr(api, "bundle", lambda: mini_bundle)
    from fastapi.testclient import TestClient
    c = TestClient(api.app)
    assert c.get("/crisis/Testville").json()["crisis"]["level"] == "watch"
    d = c.get("/donors/Testville").json()
    assert d["nearest_donors"][0]["city"] == "Richville"


def test_api_compare(monkeypatch, mini_bundle):
    import api
    monkeypatch.setattr(api, "bundle", lambda: mini_bundle)
    from fastapi.testclient import TestClient
    c = TestClient(api.app)
    r = c.post("/compare/Testville", json={"historical_date": "2026-06-01",
                                           "future_date": "2026-06-02"})
    assert r.status_code == 200
    assert r.json()["demand_change_pct"] is not None
