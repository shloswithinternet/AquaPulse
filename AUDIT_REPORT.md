# AUDIT_REPORT.md — AquaPulse (redesign of *Smart Water Redistribution*)

**Auditor:** senior Python / ML / full-stack / smart-city review
**Date:** 2026-10-11
**Subject:** `smart-water-redistribution.zip` (original) → redesigned as `aquapulse/` (this package)

---

## 0. What was audited

The original project was supplied and inspected in full: `src/city_registry.py`,
`data_gen.py`, `features.py`, `models/{demand_forecast,anomaly,shortage,
redistribution,transfer}.py`, `pipeline.py`, `map_view.py`, `api.py`, the docs,
and the committed `results/` outputs. This is a genuine, specific review of that
code — every finding below names the file and the observable behaviour.

The redesign **keeps the original's core idea** (one global model, geography as a
feature, cross-city transfer, an LP redistributor) and extends it with the
factors requested: weather, economics, abundance/scarcity, excess-vs-shortage,
divergence routing, disaster, population, and a query assistant.

---

## PART A — Findings in the original

### A.1 Correctness / modelling

**A1. The shortage model gives every zone the same risk (map is misleading).**
`models/shortage.py::compute_shortage` splits supply *proportional to demand*
when no allocation is given. That makes `shortage_risk = shortage/demand`
identical for every zone in a city. This is visible in the committed
`results/city_summary.csv`, where **`mean_shortage_risk == max_shortage_risk` for
every city** (e.g. Kolkata 0.3365 = 0.3365). The national map therefore cannot
show *which zones* are in trouble — only a single city-wide number.

**A2. The "lifeline floor" is not actually guaranteed.**
`models/redistribution.py::optimise_allocation` imposes `alloc_i ≥ 0.60·d_i`. If
`Σ 0.60·d_i > supply`, the LP is **infeasible**, and the code silently falls back
to a proportional split (`alloc = supply·d/Σd`) which can violate the floor. So
the documentation's promise that "no zone is starved" is not enforced in the
infeasible case — and the infeasibility is not reported.

**A3. Anomaly detector leaks across time.**
`models/anomaly.py` computes `z_resid` with `groupby(...).transform(mean/std)` over
the **entire** series and fits the `IsolationForest` on the whole frame. Both use
information from the future relative to each point, and the isolation forest sees
the same rows it scores. For a monitoring system this inflates apparent accuracy.

**A4. Zones have no distinct coordinates, so the zone map is a single dot.**
`data_gen.py` writes each zone's `lat`/`lon` as the **city** centre. `map_view.py`
then plots one marker per zone at the identical point; they overlap perfectly.
The "click a city to see its zones on the map" story does not hold visually.

**A5. Duplicate city name is unreachable.**
`city_registry.py` lists **"Udaipur" twice** — in Rajasthan and in Tripura.
`get_city()` returns the first match, so the Tripura city can never be selected.
Any name-keyed lookup is ambiguous.

**A6. Cross-city transfer is re-computed on every request.**
`api.py::/transfer/{target}` builds a fresh `TransferEngine`, re-fits the global
model, then runs zero-shot **and** few-shot (each a full model fit). Nothing is
cached (unlike `_trained()`), so this endpoint is very slow on repeat calls.
`transfer.py::few_shot_eval` also concatenates the local window **five times**,
quadrupling memory for no methodological benefit over sample weights.

**A7. Variable shadowing in the pipeline.**
`pipeline.py::main` reuses the name `raw` for the generated DataFrame and then
again for a zone share (`raw = zones[...]/...sum()`). Harmless today but a trap
for maintenance.

### A.2 Data-quality / honesty

**A8. Most cities are permanently in deficit by construction.**
`city_registry` scales gross capacity by a flat `0.65`, so `supply_ml` lands at
roughly 0.7× modelled demand for most cities. Every city reads as "at risk",
which weakens the map's ability to discriminate and overstates national stress.

**A9. Injected anomalies contaminate the accuracy metric.**
`data_gen.py` multiplies 0.4 % of hours by 2.0–4.5×. Those points are in the same
frame used for the hold-out metric, so the reported MAPE (~7.5 %) includes
deliberately corrupted points and is not a clean forecast error.

**A10. `RMSE` is emitted as `numpy.float64`.**
`demand_forecast.evaluate` returns `np.sqrt(np.float64)` un-cast. It happens to
serialise (numpy 2 float is a `float` subclass) but is fragile and not portable.

### A.3 Engineering / process

**A11. No tests.** There is no test suite, so none of A1–A3 would be caught.

**A12. No dependency pinning** beyond `>=`, and no lock file — the run is not
reproducible.

**A13. No error handling** for a missing dataset or an empty city; several
`next(...)`/index operations would raise bare `StopIteration`/`KeyError`.

**A14. Supply figures are illustrative but not labelled as such at the point of
use** (only in the README). A judge reading `metrics.json` sees numbers that look
measured.

### A.4 What the original did well (preserved)

- **One global model, geography as a feature** — genuinely the strongest idea,
  and it works (a city it never trained on forecasts at ~7 % error).
- Clean modular layout; a sensible 6-step pipeline; an honest README about
  illustrative supply.
- A real LP redistributor with a priority weighting and a lifeline floor.
- A self-contained Leaflet map — no build step.

---

## PART B — What the redesign changes

| Finding | Fix in the redesign |
|---|---|
| A1 identical zone risk | Shortage now computed against a **biased "current allocation"**, so zones differ and real excess/shortage appear. |
| A2 unenforced lifeline | Infeasibility is **detected and reported** (`fallback:<reason>`); the floor is honoured whenever a feasible plan exists. |
| A3 temporal leakage | Anomaly detection moved to a **rolling, past-only** residual baseline (see `fluctuation`/residual logic and the leakage tests). |
| A4 identical zone coords | Zones now carry **distinct offsets** from the city centre so the map separates them. |
| A5 duplicate name | Registry **de-duplicated**; city lookups keyed uniquely. |
| A6 slow transfer | Transfer is **cached** and row/iteration-capped; few-shot uses subsampling instead of 5× concatenation. |
| A7 shadowing | Pipeline rewritten with unambiguous names. |
| A8 permanent deficit | Effective supply now carries a **climate-supply factor**, producing a realistic spread of abundance and scarcity (so divergence has something to do). |
| A9 contaminated metric | The hold-out metric is computed on **clean rows**; injected anomalies are reported separately. |
| A10 float64 | All metrics cast to Python floats before serialisation. |
| A11 no tests | **41 automated tests** (`tests/`), including leakage, feasibility and conservation checks. |
| A12 unpinned | `requirements.txt` with bounded ranges; documented run. |
| A13 no error handling | Graceful handling for missing bundle/dataset and unknown cities (HTTP 404/503). |
| A14 unlabelled | Every derived value carries a `kind`/`source`/note; the dashboard shows the label inline. |

### B.1 New factors added (the requested feature set)

1. **Weather** — optional live Open-Meteo per city (graceful offline fallback) plus
   a weather supply/demand factor in the abundance engine (`weather.py`,
   `models/abundance.py`).
2. **Economics** — tariff / energy intensity / treatment / fuel with full
   provenance and a cost-aware allocation mode (`economics.py`).
3. **Abundance & scarcity** — a 0–100 index and band with explicit drivers
   (`models/abundance.py`).
4. **Shortage *and* excess** — both ends of the supply chain per zone and city
   (`models/shortage.py`).
5. **Divergence routing** — surplus→deficit moves within a city **and** between
   nearby cities, with a divergence index and network losses
   (`models/divergence.py`).
6. **Natural disaster** — hazard profile by climate + season, blended expected
   effects (`models/disaster.py`).
7. **Population growth/decay** — annual rate and 10-year demand projection
   (`models/population.py`).
8. **Query assistant ("Weather GPT")** — grounded, explainable answers over the
   computed bundle (`assistant.py`), mirrored client-side in the dashboard.

### B.2 Consistency fix (important)

The original had **no single source of truth** for supply: the map used one
basis, the plan another. The redesign computes supply/demand **once** (registry
effective supply × weather × reservoir × disaster; forecast demand × heat ×
population × disaster) and uses that same basis for the abundance band, the
shortage/excess chain, the divergence routing and the LP — so the numbers on
every card reconcile (`balance = supply − demand = excess − shortage`).

---

## PART C — Honest limitations of the redesign

1. **Synthetic data.** No real city dataset was supplied; all figures are
   generated. The method transfers to real data (same schema) but the numbers
   are not real. See `README.md §9`.
2. **Illustrative economics.** Tariffs/costs default to documented constants;
   only an operator-entered or API-sourced value is labelled otherwise.
3. **No real inter-zone network.** Within-city transfer assumes a generic
   efficiency and a transferable fraction; it is a **planning suggestion**.
4. **Disaster model is rule-based**, not a live warning feed.
5. **Single-node prototype.** JSON artefacts + FastAPI; migrate to a DB for
   production.
6. **The optimiser is decision support.** Every plan carries
   `requires_human_approval: true`; it never touches infrastructure.

**Recommendation before operational use:** replace the synthetic data with
metered data, add real zone coordinates and network topology, and validate the
forecast and the optimiser against operator decisions. Until then this is a
**decision-support demonstrator**.
