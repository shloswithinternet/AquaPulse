# AquaPulse — Smart Water Redistribution (redesigned)

AI-Powered Smart Water Demand Forecasting & Redistribution System

**One model for every Indian city that predicts demand, finds shortage *and*
excess, explains why with weather / economic / disaster / population factors, and
routes water from where it is surplus to where it is short.**

A redesign of the original *Smart Water Redistribution* project. It keeps the
original's best idea — **one global model, geography as a feature, no per-city
retraining** — and adds the requested factors and a multi-city dashboard.

> ⚠️ Runs on **synthetic demonstration data** (no real city dataset was
> supplied). Method transfers to real data; the numbers are illustrative.
> See `AUDIT_REPORT.md`.

---

## 1. Quick start

```bash
pip install -r requirements.txt

python src/pipeline.py            # NATIONAL run - every city in the registry (default)
python src/pipeline.py --demo     # fast 16-city benchmark

python -m pytest                  # 43 tests
```

Then **open `results/dashboard.html`** in any browser.

Optional — run the API (needed for live weather + the `/ask` endpoint):

```bash
cd src
uvicorn api:app --reload --port 8000     # open http://127.0.0.1:8000
```

### Coverage

The registry holds **584 cities, 2,665 zones, all 36 states & UTs** — the full
state-wise list. The default run monitors every one of them; `--demo` uses a
16-city benchmark for faster iteration.

The registry is **generated**, not hand-typed: `src/cities_source.py` holds the
city list, and `src/build_cities.py` looks each one up in the SimpleMaps
world-cities dataset (`data/worldcities.csv`) for **real coordinates and
populations**, then derives the climate zone, per-capita norm, supply capacity
and zone count into `src/data/cities_full.csv`. Rebuild it with
`python src/build_cities.py`. Coordinates carry a `coord_source` field
(`matched` / `manual` / `approximate`) so provenance is visible.


---

## 2. The six questions it answers

| # | Question | Where |
|---|----------|-------|
| 1 | How much water will each zone need? | `models/demand_forecast.py` |
| 2 | Is this city water-rich or water-poor, **and why**? | `models/abundance.py` |
| 3 | Who is **short** and who has **excess**? | `models/shortage.py` |
| 4 | Where should water move (excess → shortage)? | `models/divergence.py` |
| 5 | What is the best feasible allocation? | `models/redistribution.py` |
| 6 | What if a disaster / population change hits? | `models/disaster.py`, `models/population.py` |

---

## 3. The factors (the requested feature set)

- **Weather** — optional live weather per city (Open-Meteo, graceful offline
  fallback) + a rainfall/heat factor in the abundance engine.
- **Economics** — tariff, pumping energy, treatment, fuel with full provenance;
  a **cost-aware** allocation mode.
- **Abundance / scarcity** — a 0–100 index and a band, with explicit drivers.
- **Shortage *and* excess** — both ends of the supply chain, per zone and city.
- **Divergence** — surplus→deficit routing **within a city** and **between
  nearby cities**, with a divergence index and network losses.
- **Natural disaster** — hazard profile by climate + season; blended effects.
- **Population growth / decay** — annual rate and a 10-year demand projection.
- **Water Assistant ("Weather GPT")** — grounded, explainable Q&A.

---

## 4. How it flows

```
 data ─▶ features ─▶ global demand model ─▶ anomaly
                                   │
                                   ▼
            factors (weather · economics · disaster · population)
                                   │
                                   ▼
   effective supply  &  adjusted demand   ← single source of truth
                                   │
        ┌──────────────┬───────────┴───────────┬───────────────┐
        ▼              ▼                       ▼               ▼
   abundance      shortage/excess        divergence        redistribution
    index/band     supply chain          (excess→shortage)  (LP, 2 modes)
                                   │
                                   ▼
              results/bundle.json  +  results/dashboard.html  +  API
```

Every number reconciles: `balance = supply − demand = excess − shortage`.

---

## 5. The dashboard — 10 pages, charts on every one

A city search box (584 cities) plus prev/next drives every page; pages are in the
left navigation and deep-link as `#page/City`.

| Page | What it shows |
|---|---|
| 1 City Overview | national KPIs, the map (every city, coloured by risk), most-stressed table, city snapshot |
| 2 Demand Forecast | observed vs predicted chart, next-7-day forecast chart, per-zone table, **population → water ratio** (litres per capita per day vs the norm) |
| 3 Weather & Climate | live weather (with a *get live* button), stored temp/rain chart, reservoir chart, hazard-likelihood chart |
| 4 Crisis Prediction | crisis level gauge, driver chart, and the ordered **emergency plan** |
| 5 Divergence & Routing | **nearest city with an abundance of water** (distance, compass direction, surplus, deliverable), a route map, within-city moves, **essential-service protection**, zone allocation chart |
| 6 Storage & Allotment | reservoir vs reserve target chart, days of buffer, how much to **hold for a future crisis** vs release now |
| 7 Urbanization | urban-population and built-up-area projection chart, **rural/forest land converted**, the extra water demand it implies |
| 8 Compare Dates | pick a **future date** and a **historical date** and compare demand, weather and reservoir side by side |
| 9 Abnormal Consumption | flagged zone-hours chart and table, and how they feed the crisis plan |
| 10 Economics | tariffs/energy/treatment with provenance, operating cost, the two plans' cost |

A **Water Assistant** chat on every page answers questions from the computed data
(crisis, storage, urbanization, nearest donor, weather, essential services).

---

## 6. Project structure

```
aquapulse/
├── README.md  HOW_TO_EXPLAIN.md  AUDIT_REPORT.md
├── requirements.txt  run.sh
├── src/
│   ├── config.py              all tunables, units, factors, thresholds
│   ├── cities_source.py       the state-wise city list (source of truth)
│   ├── build_cities.py        matches the list to real coords -> data/cities_full.csv
│   ├── city_registry.py       loads the registry + derived factors
│   ├── data_gen.py            synthetic multi-city hourly data
│   ├── features.py            the shared feature table
│   ├── economics.py           tariffs/costs with provenance
│   ├── weather.py             optional live weather (Open-Meteo)
│   ├── assistant.py           the Water Assistant ("Weather GPT")
│   ├── pipeline.py            end-to-end run → results/
│   ├── dashboard_view.py      builds the self-contained dashboard.html
│   ├── api.py                 FastAPI backend
│   └── models/
│       ├── demand_forecast.py  global HistGB model
│       ├── anomaly.py          past-only residual + isolation forest
│       ├── shortage.py         shortage & excess supply chain
│       ├── abundance.py        abundance/scarcity engine
│       ├── crisis.py           crisis prediction + emergency plan
│       ├── storage.py          reservoir storage, reserve vs release
│       ├── essential.py        hospitals / emergency / critical protection
│       ├── urbanization.py     urban growth, rural/forest conversion
│       ├── divergence.py       excess→shortage routing + nearest donor
│       ├── disaster.py         natural-disaster factor
│       ├── population.py       growth/decay factor
│       ├── redistribution.py   LP optimiser (shortage & cost modes)
│       └── transfer.py         cross-city transfer
├── tests/                     43 tests
└── results/                   dashboard.html, bundle.json, metrics.json, CSVs
```

---

## 7. API

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | dashboard |
| GET | `/national` | national totals |
| GET | `/cities` | all demo cities + bands |
| GET | `/city/{name}` | full factor bundle for one city |
| GET | `/weather/{name}` | live weather (or clear "unavailable") |
| POST | `/scenario/{name}` | what-if: supply, demand ×, hazard, population |
| POST | `/ask` | Water Assistant query |
| POST | `/economics` | operator entry of a cost value |
| GET | `/metrics` | model evaluation |

---

## 8. Configuration

Everything tunable is in `src/config.py`: units, abundance bands, transfer
rules, disaster weights, population model, cost trade-off λ, thresholds.
Env vars: `AQUAPULSE_DISABLE_WEATHER=1`, `AQUAPULSE_RESULTS=<dir>`.

---

## 9. Honesty & limitations

- **Synthetic data.** All figures are generated; accuracy metrics describe the
  model on synthetic data only.
- **Illustrative economics.** Defaults are documented constants; only operator
  or API values are labelled otherwise.
- **No real network.** Transfers are planning suggestions with a generic
  efficiency, not a hydraulic model.
- **Disaster model is rule-based**, not a live warning.
- **Decision support only.** Every plan carries `requires_human_approval: true`;
  the optimiser never touches infrastructure.

See `AUDIT_REPORT.md` for the full audit of the original project and the
redesign, and `HOW_TO_EXPLAIN.md` for the judges' walkthrough.

---

## 10. Troubleshooting (Windows)

Two Windows-specific issues are handled in the code, but worth knowing:

- **"Windows fatal exception: access violation"** during training or tests — this
  is an OpenMP clash between numpy (MKL) and scikit-learn (libomp). `config.py`
  now sets `KMP_DUPLICATE_LIB_OK=TRUE` automatically. If it ever recurs, set it
  in your shell before running:
  `$env:KMP_DUPLICATE_LIB_OK="TRUE"; $env:OMP_NUM_THREADS="1"`.
- **`UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'`** — this
  was a real bug (files written without an explicit encoding, so Windows used
  cp1252). **Fixed**: every text read/write now specifies `encoding="utf-8"`.
  If you are on an older copy, edit `src/dashboard_view.py` line ~28 to
  `Path(out_path).write_text(html, encoding="utf-8")`.

Nothing here affects Linux or macOS.
>>>>>>> f426000 (Initial commit)
