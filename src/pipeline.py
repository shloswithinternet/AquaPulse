"""
AquaPulse Smart Water — end-to-end pipeline.

    data -> features -> global demand model -> anomaly
         -> factors (weather · economics · disaster · population · storage ·
                     essential services · urbanization)
         -> shortage & excess -> divergence (within + between cities, nearest donor)
         -> redistribution (shortage & cost modes, essential-services floor)
         -> crisis prediction & emergency plan
         -> results/bundle.json + results/dashboard.html + CSVs

Run:
    python src/pipeline.py            # national run (every city in the registry)
    python src/pipeline.py --demo     # fast 16-city benchmark
    python src/pipeline.py --refresh  # rebuild the cached feature table
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from city_registry import all_cities                                # noqa: E402
from config import DEMO_HOURS, KL_PER_ML, RESULTS_DIR               # noqa: E402
from data_gen import generate_all                                   # noqa: E402
from features import FEATURES, build_features                       # noqa: E402
from models import (abundance, crisis, disaster, divergence,        # noqa: E402
                    essential, population, storage, urbanization)
from models.anomaly import detect_anomalies, summarize_anomalies     # noqa: E402
from models.demand_forecast import GlobalDemandModel, evaluate       # noqa: E402
from models.redistribution import redistribute                       # noqa: E402
from models.shortage import (city_shortage_flags, compute_shortage,  # noqa: E402
                             supply_chain_summary, zone_demand_summary)
from models.transfer import TransferEngine                           # noqa: E402
import economics                                                     # noqa: E402

DEMO_CITIES = [
    "Mumbai", "Pune", "Ahmedabad", "Surat", "Vadodara", "Rajkot",
    "Bengaluru", "Chennai", "Kolkata", "New Delhi", "Jaipur", "Hyderabad",
    "Kochi", "Guwahati", "Srinagar", "Imphal",
]
TARGET_CITY = "Ahmedabad"
TRANSFER_TARGET = "Surat"
FORECAST_DAYS = 7


def _bias_current_allocation(zones, supply_kl, seed=7):
    """The city's existing budgeted split, which does not track demand."""
    rng = np.random.default_rng(seed)
    raw = zones["pred_daily_kl"] / zones["pred_daily_kl"].sum()
    bias = rng.lognormal(0.0, 0.25, size=len(zones))
    return supply_kl * (raw * bias) / (raw * bias).sum()


def _city_weather_historical(sub: pd.DataFrame) -> dict:
    s = sub.sort_values("timestamp")
    last = s.iloc[-1]
    recent = s.tail(72)
    return {
        "status": "historical",
        "source": "Generated historical series (not live)",
        "observed_at": str(pd.Timestamp(last["timestamp"])),
        "temperature_c": round(float(recent["temp_c"].mean()), 1),
        "rainfall_mm": round(float(recent["rain_mm"].mean()), 2),
        "humidity_pct": None,
        "forecast": [],
        "note": "Live weather is fetched per city by the API; the stored daily series is on the Weather page.",
    }


def _daily_history(daily: pd.DataFrame | None, sub: pd.DataFrame, days: int = 14) -> list[dict]:
    if daily is not None:
        d = daily[daily["city"] == sub["city"].iloc[0]].tail(days)
        rows = [(r["day"], r["observed_kl"], r["temp_c"], r["rain_mm"], r["reservoir_pct"])
                for _, r in d.iterrows()]
    else:
        d = sub.assign(day=sub["timestamp"].dt.floor("D")).groupby("day").agg(
            observed_kl=("demand_kl", "sum"), temp_c=("temp_c", "mean"),
            rain_mm=("rain_mm", "sum"), reservoir_pct=("reservoir_pct", "mean")).tail(days)
        rows = [(ix, r["observed_kl"], r["temp_c"], r["rain_mm"], r["reservoir_pct"])
                for ix, r in d.iterrows()]
    return [{"date": str(pd.Timestamp(t).date()), "observed_kl": round(float(o), 1),
             "temp_c": round(float(tc), 1), "rain_mm": round(float(rn), 1),
             "reservoir_pct": round(float(rp), 1)}
            for (t, o, tc, rn, rp) in rows]


def _daily_forecast(sub: pd.DataFrame, dow_factor: dict, growth: float,
                    days: int = FORECAST_DAYS) -> list[dict]:
    """Illustrative next-`days` daily forecast: recent mean x weekday factor x growth."""
    recent = sub.assign(day=sub["timestamp"].dt.floor("D")).groupby("day")["demand_kl"].sum()
    base = float(recent.tail(3).mean()) if len(recent) else 0.0
    last = pd.Timestamp(sub["timestamp"].max()).normalize()
    out = []
    for i in range(1, days + 1):
        day = last + pd.Timedelta(days=i)
        f = dow_factor.get(day.dayofweek, 1.0)
        val = base * f * (1.0 + growth) ** (i / 365.0)
        out.append({"date": str(day.date()), "forecast_kl": round(val, 1),
                    "weekday_factor": round(f, 3)})
    return out


def main(hours: int = DEMO_HOURS, write_dashboard: bool = True,
         all_cities_mode: bool = True, refresh: bool = False) -> dict:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cities = all_cities() if all_cities_mode else \
        [c for c in all_cities() if c["city"] in DEMO_CITIES]

    cache = RESULTS_DIR / "cache_feat.pkl"
    daily_cache = RESULTS_DIR / "cache_daily.pkl"
    daily = None
    if cache.exists() and daily_cache.exists() and not refresh:
        print("[1-2/8] Loading cached features (use --refresh to rebuild) ...")
        feat = pd.read_pickle(cache)
        daily = pd.read_pickle(daily_cache)
    else:
        print(f"[1/8] Generating {len(cities)} cities x {hours} h ...")
        raw = generate_all(cities, hours=hours)
        # daily aggregates are kept from the RAW series, so the dashboard's
        # history is the full window (the feature table drops the warm-up).
        daily = (raw.assign(day=raw["timestamp"].dt.floor("D"))
                    .groupby(["city", "day"])
                    .agg(observed_kl=("demand_kl", "sum"), temp_c=("temp_c", "mean"),
                         rain_mm=("rain_mm", "sum"), reservoir_pct=("reservoir_pct", "mean"))
                    .reset_index())
        print("[2/8] Building features ...")
        feat = build_features(raw)
        try:
            feat.to_pickle(cache); daily.to_pickle(daily_cache)
            print(f"      cached -> {cache.name}, {daily_cache.name}")
        except Exception as exc:
            print("      (cache skipped:", exc, ")")
    print(f"      rows={len(feat):,}  features={len(FEATURES)}")

    print("[3/8] Training the global demand model ...")
    cut = feat["timestamp"].max() - pd.Timedelta(hours=48)
    train, test = feat[feat["timestamp"] < cut], feat[feat["timestamp"] >= cut]
    Xtr = train[FEATURES].to_numpy(float)
    ytr = train["demand_kl"].to_numpy(float)
    if len(Xtr) > 60000:
        idx = np.random.default_rng(0).choice(len(Xtr), 60000, replace=False)
        Xtr, ytr = Xtr[idx], ytr[idx]
    model = GlobalDemandModel().fit(Xtr, ytr)
    overall = evaluate(test["demand_kl"].to_numpy(float),
                       model.predict(test[FEATURES].to_numpy(float)))
    print("      holdout:", overall)
    feat["pred_demand"] = model.predict(feat[FEATURES].to_numpy(float))

    print("[4/8] Anomaly detection ...")
    feat = detect_anomalies(feat)
    anom = summarize_anomalies(feat)
    print(f"      flagged zone-hours: {int(feat['is_anomaly'].sum()):,}")

    # weekday shape, used by the illustrative daily forecast
    tmp = feat.assign(dow=feat["timestamp"].dt.dayofweek)
    dow_mean = tmp.groupby("dow")["demand_kl"].mean()
    dow_factor = {int(k): round(float(v / dow_mean.mean()), 3) for k, v in dow_mean.items()}

    print("[5/8] Transfer evaluation ...")
    engine = TransferEngine(DEMO_CITIES).fit_global(feat)
    zs = engine.zero_shot_eval(feat, TRANSFER_TARGET)
    fs = engine.few_shot_eval(feat, TRANSFER_TARGET, n_days=7)
    donors_t = engine.nearest_donors(feat, TRANSFER_TARGET, k=3)
    print(f"      {TRANSFER_TARGET} zero-shot {zs}")

    print("[6/8] Per-city factors, plans and divergence ...")
    econ_state = economics.get_state()
    cost_per_kl_default = economics.operating_cost_per_kl(
        econ_state["by_name"]["electricity_tariff_inr_per_kwh"]["value"],
        econ_state["by_name"]["treatment_cost_inr_per_kl"]["value"],
        econ_state["by_name"]["energy_intensity_kwh_per_kl"]["value"])

    city_bundles = []
    groups = {name: g for name, g in feat.groupby("city")}
    for c in cities:
        sub = groups.get(c["city"])
        if sub is None or sub.empty:
            continue
        zones = zone_demand_summary(sub)
        raw_demand = float(zones["pred_daily_kl"].sum())

        pop = population.analyse(c)
        dis = disaster.analyse(c)
        wx = _city_weather_historical(sub)
        recent = sub.sort_values("timestamp").tail(72)
        res_pct = float(recent["reservoir_pct"].mean())
        ab = abundance.analyse(c, raw_demand, c["supply_ml"],
                               rain_mm=float(recent["rain_mm"].mean()),
                               temp_c=float(recent["temp_c"].mean()),
                               reservoir_pct=res_pct,
                               disaster=dis, population=pop, econ=econ_state)

        zones["pred_daily_kl"] = zones["pred_daily_kl"] * ab["demand_factor"]
        eff_supply_ml = c["supply_ml"] * ab["supply_factor"]
        eff_supply_kl = eff_supply_ml * KL_PER_ML

        # essential services (before planning, so the optimiser can protect them)
        ess = essential.analyse(c, zones.to_dict("records"), float(zones["pred_daily_kl"].sum()))

        current = _bias_current_allocation(zones, eff_supply_kl)
        zones = compute_shortage(zones, eff_supply_ml, allocation_kl=current)
        zones = city_shortage_flags(zones)
        chain = supply_chain_summary(zones)

        rec, rec_info = redistribute(zones, eff_supply_ml, mode="shortage",
                                     essential_fraction=ess["essential_share"],
                                     essential_zones=set(ess["essential_zones"]))
        rec_cost, cost_info = redistribute(zones, eff_supply_ml, mode="cost",
                                           cost_per_kl=np.full(len(zones), cost_per_kl_default),
                                           lambda_cost=0.15,
                                           essential_fraction=ess["essential_share"],
                                           essential_zones=set(ess["essential_zones"]))
        div = divergence.route_within_city(zones)
        store = storage.analyse(c, res_pct, eff_supply_ml, chain["total_demand_kl"],
                                essential_share=ess["essential_share"])
        op_cost = economics.estimate_operating_cost(chain["total_demand_kl"], econ_state)
        urb = urbanization.analyse(c, chain["total_demand_kl"])

        # real-time population -> water ratio (litres per capita per day)
        lpcd_now = (chain["total_demand_kl"] * 1000.0 / (c["pop_millions"] * 1e6)
                    if c["pop_millions"] > 0 else 0.0)
        lpcd_gap = lpcd_now - c["lpcd_norm"]

        # anomalies for this city
        a_sub = sub[sub["is_anomaly"]].sort_values("anomaly_score", ascending=False).head(8)
        anomalies = [{"zone_id": r["zone_id"], "time": str(pd.Timestamp(r["timestamp"]))[:16],
                      "observed_kl": round(float(r["demand_kl"]), 1),
                      "expected_kl": round(float(r["pred_demand"]), 1),
                      "z": round(float(r["z_resid"]), 2) if pd.notna(r["z_resid"]) else None,
                      "score": round(float(r["anomaly_score"]), 2) if pd.notna(r["anomaly_score"]) else 0.5,
                      "direction": "up" if r["demand_kl"] >= r["pred_demand"] else "down"}
                     for _, r in a_sub.iterrows()]

        cr = crisis.analyse(c, chain, ab, dis, store, anomalies, pop)

        trend_df = (sub.assign(day=sub["timestamp"].dt.floor("D"))
                       .groupby("day")[["demand_kl", "pred_demand"]].mean().round(2).tail(14))
        trend = [{"date": str(d.date()), "observed": float(r["demand_kl"]),
                  "predicted": float(r["pred_demand"])} for d, r in trend_df.iterrows()]

        zone_records = []
        for _, z in rec.sort_values("pred_daily_kl", ascending=False).iterrows():
            ratio = (z["balance_kl"] / z["pred_daily_kl"]) if z["pred_daily_kl"] > 0 else 0.0
            zone_records.append({
                "zone_id": z["zone_id"], "lat": float(z["lat"]), "lon": float(z["lon"]),
                "pred_daily_kl": round(float(z["pred_daily_kl"]), 1),
                "pred_peak_kl": round(float(z["pred_peak_kl"]), 1),
                "obs_daily_kl": round(float(z["obs_daily_kl"]), 1),
                "supply_kl": round(float(z["supply_kl"]), 1),
                "shortage_kl": round(float(z["shortage_kl"]), 1),
                "excess_kl": round(float(z["excess_kl"]), 1),
                "balance_kl": round(float(z["balance_kl"]), 1),
                "shortage_risk": round(float(z["shortage_risk"]), 4),
                "at_risk": bool(z["at_risk"]), "has_surplus": bool(z["has_surplus"]),
                "abundance_band": abundance.classify(ratio),
                "essential": z["zone_id"] in ess["essential_zones"],
                "recommended_supply_kl": round(float(z["recommended_supply_kl"]), 1),
                "recommended_unmet_kl": round(float(z["recommended_unmet_kl"]), 1),
                "recommended_shortage_risk": round(float(z["recommended_shortage_risk"]), 4),
            })

        baseline_unmet = float(zones["shortage_kl"].sum())
        optimised_unmet = float(rec_info["total_unmet_kl"])
        city_bundles.append({
            "city": c["city"], "state_ut": c["state_ut"], "lat": c["lat"], "lon": c["lon"],
            "climate_zone": c["climate_zone"], "pop_millions": c["pop_millions"],
            "supply_ml": c["supply_ml"], "gross_supply_ml": c["gross_supply_ml"],
            "effective_supply_ml": round(eff_supply_ml, 1),
            "n_zones": c["n_zones"], "growth_rate": c["growth_rate"],
            "reservoir_baseline_pct": c["reservoir_baseline_pct"],
            "coord_source": c.get("coord_source", "matched"),
            "weather": wx, "disaster": dis, "population": pop, "abundance": ab,
            "shortage": chain, "divergence": div, "storage": store,
            "essential": ess, "urbanization": urb, "crisis": cr,
            "operating_cost": op_cost,
            "population_water": {
                "pop_millions": c["pop_millions"], "demand_kl": round(chain["total_demand_kl"], 1),
                "lpcd_now": round(lpcd_now, 1), "lpcd_norm": c["lpcd_norm"],
                "gap_lpcd": round(lpcd_gap, 1),
                "ratio_index": round(min(max(100.0 * lpcd_now / max(c["lpcd_norm"], 1.0), 0), 200), 1),
                "note": "Litres per capita per day, computed live from the forecast demand.",
            },
            "plan": {
                "mode": "shortage", "lp_status": rec_info["status"],
                "baseline_unmet_kl": round(baseline_unmet, 1),
                "optimised_unmet_kl": round(optimised_unmet, 1),
                "unmet_reduction_pct": round(100 * (baseline_unmet - optimised_unmet) /
                                             max(baseline_unmet, 1e-9), 1),
                "max_risk_before": round(float(zones["shortage_risk"].max()), 4),
                "max_risk_after": round(float(rec["recommended_shortage_risk"].max()), 4),
                "essential_floor_kl": ess["protection_floor_kl"],
                "requires_human_approval": True,
            },
            "plan_cost": {"mode": "cost", "lp_status": cost_info["status"],
                          "optimised_unmet_kl": round(float(cost_info["total_unmet_kl"]), 1),
                          "cost_per_kl_inr": round(cost_per_kl_default, 3)},
            "zones": zone_records, "trend": trend, "anomalies": anomalies,
            "history_daily": _daily_history(daily, sub),
            "forecast_daily": _daily_forecast(sub, dow_factor, c["growth_rate"]),
        })

    print("[7/8] Nearest-donor divergence and national summary ...")
    # second pass: nearest city with a surplus, for every city that has a deficit
    cand = [{"city": b["city"], "lat": b["lat"], "lon": b["lon"],
             "excess_kl": max(b["shortage"]["total_supply_kl"] - b["shortage"]["total_demand_kl"], 0.0),
             "band": b["abundance"]["band"]} for b in city_bundles]
    for b in city_bundles:
        need = max(b["shortage"]["total_shortage_kl"], 0.0)
        b["nearest_donors"] = divergence.nearest_donors(b, cand, k=3) if need > 0 else []
        b["residual_shortage_kl"] = b["divergence"]["residual_shortage_kl"]

    cross_inputs = [{"city": b["city"], "lat": b["lat"], "lon": b["lon"],
                     "residual_shortage_kl": b["divergence"]["residual_shortage_kl"],
                     "surplus_kl": max(b["shortage"]["total_supply_kl"] -
                                       b["shortage"]["total_demand_kl"], 0.0) * 0.5}
                    for b in city_bundles]
    cross = divergence.route_between_cities(cross_inputs)

    crisis_counts = Counter(b["crisis"]["level"] for b in city_bundles)
    national = {
        "n_cities": len(city_bundles),
        "n_states_ut": len({b["state_ut"] for b in city_bundles}),
        "n_zones": int(sum(b["n_zones"] for b in city_bundles)),
        "total_demand_kl": round(sum(b["shortage"]["total_demand_kl"] for b in city_bundles), 1),
        "total_supply_kl": round(sum(b["shortage"]["total_supply_kl"] for b in city_bundles), 1),
        "total_shortage_kl": round(sum(b["shortage"]["total_shortage_kl"] for b in city_bundles), 1),
        "total_excess_kl": round(sum(b["shortage"]["total_excess_kl"] for b in city_bundles), 1),
        "at_risk_zones": int(sum(1 for b in city_bundles for z in b["zones"] if z["at_risk"])),
        "essential_zones": int(sum(len(b["essential"]["essential_zones"]) for b in city_bundles)),
        "divergence_index": round(float(np.mean([b["divergence"]["divergence_index"]
                                                 for b in city_bundles])), 4),
        "crisis_levels": dict(crisis_counts),
        "cities_in_crisis": crisis_counts.get("warning", 0) + crisis_counts.get("emergency", 0),
        "cross_city_transfers": cross,
    }

    metrics = {
        "overall_holdout": overall,
        "transfer": {"target_city": TRANSFER_TARGET, "zero_shot": zs,
                     "few_shot_7d": fs, "donors": donors_t},
        "target_city": TARGET_CITY,
        "national": {k: national[k] for k in
                     ("n_cities", "n_states_ut", "n_zones", "total_demand_kl",
                      "total_shortage_kl", "total_excess_kl", "at_risk_zones",
                      "cities_in_crisis")},
    }
    (RESULTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    bundle = {
        "meta": {"data_source": "Synthetic consumption series; real city coordinates "
                                 "and populations (SimpleMaps world-cities).",
                 "generated_cities": [b["city"] for b in city_bundles],
                 "target_city": TARGET_CITY, "transfer_target": TRANSFER_TARGET,
                 "units": {"volume": "kL/day", "supply_ml": "million litres/day",
                           "tariff": "INR/kWh", "cost": "INR", "per_capita": "litres/day"},
                 "model": "HistGradientBoostingRegressor (one global model, all cities)"},
        "metrics": metrics, "national": national, "economics": econ_state,
        "cities": city_bundles,
    }
    (RESULTS_DIR / "bundle.json").write_text(json.dumps(bundle, separators=(",", ":")), encoding="utf-8")
    print("      wrote results/bundle.json")

    rows = [{"city": b["city"], "state_ut": b["state_ut"], "climate_zone": b["climate_zone"],
             "pop_millions": b["pop_millions"], "supply_ml": b["supply_ml"],
             "demand_kl": b["shortage"]["total_demand_kl"],
             "shortage_kl": b["shortage"]["total_shortage_kl"],
             "excess_kl": b["shortage"]["total_excess_kl"],
             "worst_risk": b["shortage"]["worst_zone_risk"],
             "abundance_band": b["abundance"]["band"],
             "crisis_level": b["crisis"]["level"], "crisis_score": b["crisis"]["score"],
             "disaster_risk": b["disaster"]["disaster_risk"],
             "growth_pct": b["population"]["annual_growth_pct"],
             "days_of_buffer": b["storage"]["days_of_buffer"],
             "divergence_index": b["divergence"]["divergence_index"],
             "nearest_donor": (b["nearest_donors"][0]["city"] if b["nearest_donors"] else ""),
             "unmet_reduction_pct": b["plan"]["unmet_reduction_pct"]} for b in city_bundles]
    pd.DataFrame(rows).sort_values("worst_risk", ascending=False).to_csv(
        RESULTS_DIR / "city_summary.csv", index=False, encoding="utf-8")
    anom.head(100).to_csv(RESULTS_DIR / "top_anomalies.csv", index=False, encoding="utf-8")

    if write_dashboard:
        print("[8/8] Building dashboard ...")
        from dashboard_view import build_dashboard
        build_dashboard(bundle, RESULTS_DIR / "dashboard.html")

    print("\nDone. Open results/dashboard.html (or run the API).")
    return bundle


if __name__ == "__main__":
    args = sys.argv[1:]
    refresh = "--refresh" in args
    if "--demo" in args:
        main(hours=DEMO_HOURS, all_cities_mode=False, refresh=refresh)
    else:
        hours = 24 * 10
        for a in args:
            if a.startswith("--hours="):
                hours = int(a.split("=")[1])
        main(hours=hours, all_cities_mode=True, refresh=refresh)
