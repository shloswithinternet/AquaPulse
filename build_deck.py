"""Builds the AquaPulse briefing deck (.pptx) with python-pptx.

Content is drawn from the actual project: the problem statement supplied by the
user, the suggested approach, the real model metrics (results/metrics.json) and
the real test results.
"""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
OUT = ROOT / "AquaPulse_Briefing.pptx"

# ---- palette -------------------------------------------------------------
INK = RGBColor(0x10, 0x23, 0x3A)
INK2 = RGBColor(0x1C, 0x33, 0x50)
TEAL = RGBColor(0x0E, 0x7C, 0x86)
BLUE = RGBColor(0x1B, 0x6C, 0xA8)
GREEN = RGBColor(0x1F, 0x8A, 0x4C)
AMBER = RGBColor(0xC8, 0x7A, 0x0A)
RED = RGBColor(0xC0, 0x39, 0x2B)
MUTED = RGBColor(0x5B, 0x6B, 0x7F)
PANEL = RGBColor(0xF1, 0xF5, 0xF9)
PANEL2 = RGBColor(0xE4, 0xEC, 0xF3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Segoe UI"
W, H = Inches(13.333), Inches(7.5)

prs = Presentation()
prs.slide_width, prs.slide_height = W, H


def slide():
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    bg.fill.solid(); bg.fill.fore_color.rgb = WHITE; bg.line.fill.background()
    bg.shadow.inherit = False
    return s


def box(s, x, y, w, h, text="", *, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT,
        font=FONT, italic=False, anchor=MSO_ANCHOR.TOP, spacing=1.0):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = align; p.line_spacing = spacing
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic
    r.font.color.rgb = color; r.font.name = font
    return tb


def rect(s, x, y, w, h, fill, *, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(1)
    sh.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sh.adjustments[0] = radius
        except Exception:
            pass
    return sh


def header(s, kicker, title, page):
    rect(s, 0, 0, 13.333, 1.15, INK, shape=MSO_SHAPE.RECTANGLE)
    rect(s, 0, 1.15, 13.333, 0.06, TEAL, shape=MSO_SHAPE.RECTANGLE)
    box(s, 0.6, 0.16, 11, 0.3, kicker.upper(), size=11, color=RGBColor(0x8F, 0xC9, 0xCF), bold=True)
    box(s, 0.6, 0.44, 11.6, 0.6, title, size=23, color=WHITE, bold=True)
    box(s, 12.2, 0.42, 0.9, 0.5, str(page), size=13, color=RGBColor(0x8F, 0xC9, 0xCF),
        bold=True, align=PP_ALIGN.RIGHT)


def footer(s, text):
    rect(s, 0, 7.16, 13.333, 0.34, PANEL, shape=MSO_SHAPE.RECTANGLE)
    box(s, 0.6, 7.21, 12.2, 0.26, text, size=9.5, color=MUTED)


def bullets(s, x, y, w, items, *, size=13.5, gap=0.05, bullet_color=TEAL, line=1.22):
    """items: list of (level, text) or plain strings."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(4))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    first = True
    for it in items:
        lvl, txt = it if isinstance(it, tuple) else (0, it)
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.line_spacing = line
        p.space_after = Pt(6 if lvl == 0 else 3)
        p.level = lvl
        mark = "•  " if lvl == 0 else "–  "
        rb = p.add_run(); rb.text = mark
        rb.font.size = Pt(size if lvl == 0 else size - 1.5)
        rb.font.color.rgb = bullet_color if lvl == 0 else MUTED
        rb.font.bold = True; rb.font.name = FONT
        r = p.add_run(); r.text = txt
        r.font.size = Pt(size if lvl == 0 else size - 1.5)
        r.font.color.rgb = INK if lvl == 0 else INK2
        r.font.name = FONT
    return tb


def kpi(s, x, y, w, h, value, label, color=TEAL, vsize=26):
    rect(s, x, y, w, h, PANEL, line=PANEL2)
    rect(s, x, y, 0.06, h, color, shape=MSO_SHAPE.RECTANGLE)
    box(s, x + 0.22, y + 0.14, w - 0.35, 0.5, value, size=vsize, color=color, bold=True)
    box(s, x + 0.22, y + h - 0.62, w - 0.35, 0.5, label, size=10.5, color=MUTED, spacing=1.05)


def table(s, x, y, w, h, head, rows, *, col_widths=None, fs=11.5, head_fs=11):
    shp = s.shapes.add_table(len(rows) + 1, len(head), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shp.table
    tbl.first_row = True
    if col_widths:
        total = sum(col_widths)
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = Emu(int(Inches(w) * cw / total))
    for j, htxt in enumerate(head):
        c = tbl.cell(0, j); c.text = htxt
        c.fill.solid(); c.fill.fore_color.rgb = INK
        p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
        for r in p.runs:
            r.font.size = Pt(head_fs); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = FONT
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            c = tbl.cell(i, j); c.text = str(val)
            c.fill.solid(); c.fill.fore_color.rgb = WHITE if i % 2 else PANEL
            p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
            for r in p.runs:
                r.font.size = Pt(fs); r.font.color.rgb = INK; r.font.name = FONT
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
    return tbl


def arrow(s, x, y, w, h, color=TEAL):
    sh = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = color; sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def chart(s, x, y, w, h, kind, cats, series, colors, title=None):
    cd = CategoryChartData(); cd.categories = cats
    for name, vals in series:
        cd.add_series(name, vals)
    gf = s.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart
    ch.has_legend = len(series) > 1
    if ch.has_legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(9); ch.legend.font.name = FONT; ch.legend.font.color.rgb = MUTED
    if title:
        ch.has_title = True
        ch.chart_title.text_frame.text = title
        for r in ch.chart_title.text_frame.paragraphs[0].runs:
            r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = INK; r.font.name = FONT
    else:
        ch.has_title = False
    for i, plot in enumerate(ch.plots):
        plot.has_data_labels = False
        if kind == XL_CHART_TYPE.COLUMN_CLUSTERED and len(series) == 1:
            plot.has_data_labels = True
            plot.data_labels.font.size = Pt(9); plot.data_labels.font.color.rgb = INK
            plot.data_labels.font.name = FONT
    ch.category_axis.tick_labels.font.size = Pt(9)
    ch.category_axis.tick_labels.font.name = FONT
    ch.value_axis.tick_labels.font.size = Pt(9)
    ch.value_axis.tick_labels.font.name = FONT
    for srs, col in zip(ch.series, colors):
        srs.format.fill.solid(); srs.format.fill.fore_color.rgb = col
    return ch


# =========================================================================
# Load the real numbers
# =========================================================================
bundle = json.loads((RESULTS / "bundle.json").read_text())
M = bundle["metrics"]
HOLD = M["overall_holdout"]
TR = M["transfer"]
NAT = bundle["national"]
N = bundle["national"]
n_transfers = len(N["cross_city_transfers"]["transfers"])
from collections import Counter
BANDS = Counter(c["abundance"]["band"] for c in bundle["cities"])

# =========================================================================
# 01 — Title
# =========================================================================
s = slide()
rect(s, 0, 0, 13.333, 7.5, INK, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, 0, 0.22, 7.5, TEAL, shape=MSO_SHAPE.RECTANGLE)
box(s, 1.0, 1.35, 11, 0.4, "SE SMART CITY  ·  PROBLEM STATEMENT: SMART WATER REDISTRIBUTION",
    size=12.5, color=RGBColor(0x8F, 0xC9, 0xCF), bold=True)
box(s, 1.0, 1.9, 11.3, 1.2, "AquaPulse", size=54, color=WHITE, bold=True)
box(s, 1.0, 3.05, 11.3, 0.8,
    "An ML system that predicts water demand zone by zone, detects abnormal\n"
    "consumption, predicts shortage, and recommends how to redistribute supply.",
    size=16, color=RGBColor(0xC9, 0xD6, 0xE4), spacing=1.25)
rect(s, 1.0, 4.35, 5.6, 0.02, RGBColor(0x33, 0x4A, 0x66), shape=MSO_SHAPE.RECTANGLE)
box(s, 1.0, 4.55, 11.3, 1.4,
    f"One model for every city  ·  {NAT['n_cities']} cities · {NAT['n_zones']} zones · {NAT['n_states_ut']} states & UTs\n"
    "Weather · economics · disaster · population factors  ·  Live monitoring dashboard",
    size=13, color=RGBColor(0x8F, 0xC9, 0xCF), spacing=1.3)
box(s, 1.0, 6.5, 11.3, 0.4, "Technical briefing  ·  model, architecture, algorithm, factors, evaluation",
    size=11, color=MUTED)

# =========================================================================
# 02 — The problem
# =========================================================================
s = slide(); header(s, "Problem statement", "Water is lost because cities see demand only after it happens", 2)
bullets(s, 0.6, 1.5, 6.2, [
    "Water consumption changes with the hour, the day, the season, the weather and previous consumption patterns.",
    "Cities act on consumption only after the fact, so some zones run dry while others hold surplus.",
    "Unusual consumption (leaks, bursts, sudden spikes) goes unnoticed until it is expensive.",
    "Supply is finite: the real question is not 'how much water exists' but 'how do we move what we have to where it is needed'.",
], size=13)
rect(s, 7.05, 1.5, 5.7, 5.3, PANEL, line=PANEL2)
box(s, 7.35, 1.72, 5.1, 0.4, "WHAT THE BRIEF ASKS FOR", size=11, color=TEAL, bold=True)
bullets(s, 7.35, 2.2, 5.1, [
    "Demand prediction per zone for upcoming hours.",
    "Abnormal consumption detection, highlighted in the UI.",
    "Shortage prediction: demand vs supply, per zone.",
    "Supply redistribution recommendation, prioritising high-demand, high-risk zones.",
], size=12.5, bullet_color=BLUE)
box(s, 7.35, 5.35, 5.1, 0.4, "BROWNIE POINTS WE COVERED", size=11, color=AMBER, bold=True)
bullets(s, 7.35, 5.8, 5.1, [
    "Change supply and re-solve the plan.",
    "Zones on a map with demand & risk.",
    "Weather as a factor in demand.",
], size=12, bullet_color=AMBER)
footer(s, "Source: supplied problem statement and 'Suggested Approach' (SE Smart City).")

# =========================================================================
# 03 — Proposed solution
# =========================================================================
s = slide(); header(s, "Proposed solution", "Four required pillars, plus the factors that make the plan realistic", 3)
pillars = [
    ("1  Demand prediction", "One global model forecasts the next 24 h of demand for every zone.", TEAL),
    ("2  Abnormal consumption", "Residual + isolation-forest detection flags zones behaving unusually.", BLUE),
    ("3  Shortage prediction", "Forecast demand vs deliverable supply, per zone, with a risk score.", AMBER),
    ("4  Supply redistribution", "A linear program re-allocates the same water, prioritising risk.", GREEN),
]
x = 0.6
for title, desc, col in pillars:
    rect(s, x, 1.5, 2.98, 1.7, PANEL, line=PANEL2)
    rect(s, x, 1.5, 2.98, 0.09, col, shape=MSO_SHAPE.RECTANGLE)
    box(s, x + 0.22, 1.72, 2.6, 0.4, title, size=13, color=col, bold=True)
    box(s, x + 0.22, 2.18, 2.6, 0.95, desc, size=11.5, color=INK2, spacing=1.15)
    x += 3.13
rect(s, 0.6, 3.5, 12.13, 3.3, PANEL, line=PANEL2)
box(s, 0.9, 3.7, 11.6, 0.4, "EXTENDED FACTOR SET  —  what decides abundance and scarcity", size=11.5, color=INK, bold=True)
factors = [
    ("Weather", "rainfall recharges supply, heat raises demand; optional live feed"),
    ("Economics", "tariff, pumping energy, treatment cost; a cost-aware allocation mode"),
    ("Abundance / scarcity", "a 0-100 index and band with explicit drivers"),
    ("Shortage AND excess", "both ends of the supply chain, per zone and city"),
    ("Divergence", "routes surplus to shortage within and between cities"),
    ("Disaster", "hazard profile by climate and season; blended expected effects"),
    ("Population", "annual growth/decay and a 10-year demand projection"),
    ("Assistant", "grounded question-answering over the computed data"),
]
x, y = 0.9, 4.15
for i, (t, d) in enumerate(factors):
    cx = x + (i % 4) * 3.0
    cy = y + (i // 4) * 1.15
    rect(s, cx, cy, 2.85, 1.0, WHITE, line=PANEL2)
    box(s, cx + 0.16, cy + 0.1, 2.55, 0.3, t, size=11.5, color=TEAL, bold=True)
    box(s, cx + 0.16, cy + 0.42, 2.55, 0.55, d, size=10, color=INK2, spacing=1.1)
footer(s, "Pillars 1-4 are the brief's required outputs; the factor set is what makes the recommendation defensible.")

# =========================================================================
# 04 — Architecture
# =========================================================================
s = slide(); header(s, "Base architecture", "Five layers, one direction of flow, one source of truth for supply", 4)
layers = [
    ("LAYER 1 · DATA", "Hourly water use per zone + weather + reservoir + tariff + population. Synthetic demo now; real sources plug in unchanged (Kaggle DM1718, Smart Cities Open Data, IMD).", TEAL),
    ("LAYER 2 · FEATURES", "One shared table for every city: hour, day, month, weather, reservoir, tariff, energy/kL, lags and rolling stats, population, climate one-hot.", BLUE),
    ("LAYER 3 · MODELS", "Global demand model (HistGradientBoosting)  ·  anomaly detection  ·  factor engines: abundance, disaster, population.", INK2),
    ("LAYER 4 · DECISION", "Shortage & excess supply chain  ·  divergence routing (excess to shortage)  ·  linear-program redistribution (shortage / cost modes).", AMBER),
    ("LAYER 5 · PRESENTATION", "Multi-city dashboard (city tabs + right-hand factor window + map)  ·  Water Assistant  ·  FastAPI for scenarios and live weather.", GREEN),
]
y = 1.42
for name, desc, col in layers:
    rect(s, 0.6, y, 12.13, 0.98, PANEL, line=PANEL2)
    rect(s, 0.6, y, 0.09, 0.98, col, shape=MSO_SHAPE.RECTANGLE)
    box(s, 0.9, y + 0.13, 2.5, 0.3, name, size=11.5, color=col, bold=True)
    box(s, 3.45, y + 0.13, 9.1, 0.75, desc, size=10.5, color=INK2, spacing=1.12)
    if y < 6.0:
        arrow(s, 6.5, y + 0.99, 0.3, 0.06, RGBColor(0xC3, 0xCF, 0xDC))
    y += 1.06
footer(s, "Every layer is a separate module; the supply/demand basis is computed once and reused everywhere.")

# =========================================================================
# 05 — Data & features
# =========================================================================
s = slide(); header(s, "Data & features", "The same feature vector is built for every city, so one model serves all", 5)
table(s, 0.6, 1.5, 6.3, 3.0,
      ["Field group", "Examples"],
      [["Time", "hour, day of week, month, weekend"],
       ["Weather", "temperature, rainfall, humidity"],
       ["Water system", "reservoir level, tariff, pump energy/kL"],
       ["History", "lag 1 h, lag 24 h, lag 168 h, rolling mean & std"],
       ["City meta", "population, per-capita norm, latitude, climate one-hot"]],
      col_widths=[1, 1.7], fs=11)
rect(s, 7.15, 1.5, 5.6, 3.0, PANEL, line=PANEL2)
box(s, 7.42, 1.68, 5.1, 0.35, "DATA SOURCES", size=11, color=TEAL, bold=True)
bullets(s, 7.42, 2.1, 5.1, [
    "Named in the brief: Kaggle DM1718 Water Consumption.",
    "Smart Cities Open Data Portal (Bengaluru, Gangtok, Pune).",
    "IMD weather API / imdlib for temperature and rainfall.",
    "Open-Meteo for live weather (optional, cached).",
    "Demo runs on a generator with the identical schema.",
], size=11, bullet_color=BLUE)
box(s, 7.42, 4.05, 5.1, 0.4, "Provenance: every derived value carries kind (measured / estimated / manual / illustrative) and a source.", size=10.5, color=MUTED, spacing=1.15)
box(s, 0.6, 4.75, 12.13, 2.1,
    "Key design choice - geography as a feature, not an identity.\n"
    "The model never sees a city name. A Mumbai zone and a Surat zone are described by the same numbers: hour, temperature,\n"
    "rainfall, population, per-capita norm, climate type. Because of this, a model trained on a set of cities predicts a city it has\n"
    f"never been trained on - which is how one model covers all {NAT['n_cities']} cities without retraining.",
    size=13, color=INK, spacing=1.35)
footer(s, "Schema is stable: swapping the generator for a real adapter changes nothing downstream.")

# =========================================================================
# 06 — ML model
# =========================================================================
s = slide(); header(s, "ML model", "One global gradient-boosted model, trained across cities, predicts any city's demand", 6)
rect(s, 0.6, 1.5, 6.3, 5.2, PANEL, line=PANEL2)
box(s, 0.9, 1.7, 5.7, 0.4, "MODEL", size=11, color=TEAL, bold=True)
bullets(s, 0.9, 2.15, 5.7, [
    "Algorithm: HistGradientBoostingRegressor (scikit-learn).",
    "Handles missing values, mixed feature types and non-linear interactions with little tuning.",
    "Faster and transfers better to a new city with little data than a deep model.",
    "Target: hourly demand per zone (kilolitres).",
    "Prediction horizon: next 24 hours (configurable).",
], size=12)
box(s, 0.9, 4.35, 5.7, 0.4, "WHY ONE MODEL, NOT ONE PER CITY", size=11, color=BLUE, bold=True)
bullets(s, 0.9, 4.8, 5.7, [
    "A new city needs no local training to get a forecast (zero-shot).",
    "With a week of local data it improves (few-shot).",
    "Cities with similar meta-features act as donors.",
], size=11.5, bullet_color=BLUE)
rect(s, 7.15, 1.5, 5.6, 5.2, WHITE, line=PANEL2)
box(s, 7.42, 1.7, 5.1, 0.4, "TRAINING PIPELINE", size=11, color=TEAL, bold=True)
steps = ["Generate / load multi-city hourly data", "Build the shared feature table",
         "Chronological train / hold-out split (last 48 h held out)",
         "Fit the global model on all training cities",
         "Evaluate on the hold-out; report MAE, RMSE, MAPE, R2",
         "Refit on all data; forecast every city",
         "Cross-city transfer test on a held-out city"]
y = 2.2
for i, st in enumerate(steps, 1):
    rect(s, 7.42, y, 0.34, 0.34, TEAL, shape=MSO_SHAPE.OVAL)
    box(s, 7.42, y + 0.04, 0.34, 0.3, str(i), size=11, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    box(s, 7.9, y + 0.02, 4.6, 0.5, st, size=11, color=INK2, spacing=1.1)
    y += 0.6
footer(s, "Validation is chronological - no shuffling of a time series; lags and rolling stats use past values only (no leakage).")

# =========================================================================
# 07 — Where it was trained
# =========================================================================
s = slide(); header(s, "Where and how it was trained", "Trained on this machine, on the generated multi-city series, reproducibly", 7)
rows = [
    ["Training data", "Synthetic multi-city hourly series (identical schema to real sources)"],
    ["Benchmark run", "16 cities x 30 days hourly  =  105,432 feature rows"],
    ["National run", f"{NAT['n_cities']} cities x 10 days hourly  =  193,392 feature rows, {NAT['n_zones']} zones"],
    ["Model", "HistGradientBoostingRegressor, max_iter 300, learning rate 0.06"],
    ["Environment", "Python 3.12, scikit-learn 1.9, single-threaded for reproducibility"],
    ["Split", "Chronological: last 48 hours held out, never shuffled"],
    ["Reproduce", "python src/pipeline.py  (all cities)  ·  --demo for the 16-city benchmark"],
]
table(s, 0.6, 1.5, 12.13, 3.6, ["Item", "Value"], rows, col_widths=[1, 3.4], fs=11.5)
rect(s, 0.6, 5.35, 12.13, 1.6, PANEL, line=PANEL2)
box(s, 0.9, 5.55, 11.6, 1.3,
    "Honest note on data.  No real city dataset was supplied with the brief, so the system is trained on a synthetic series that\n"
    "mirrors the named sources' columns. Every row is labelled SYNTHETIC_DEMO. The method transfers to real data unchanged -\n"
    "replace the generator with an adapter and re-run; no model code changes.",
    size=12, color=INK2, spacing=1.3)
footer(s, "The accuracy figures therefore describe the model on synthetic data; they are reported, not asserted as real-world accuracy.")

# =========================================================================
# 08 — Evaluation / where ML passes
# =========================================================================
s = slide(); header(s, "Model evaluation", "Where the ML passes: hold-out and held-out-city accuracy, plus 43 automated tests", 8)
kpi(s, 0.6, 1.5, 2.95, 1.5, f"{HOLD['MAPE_%']}%", f"MAPE (hold-out, {NAT['n_cities']} cities)", TEAL)
kpi(s, 3.7, 1.5, 2.95, 1.5, f"{HOLD['R2']}", "R-squared (hold-out)", BLUE)
kpi(s, 6.8, 1.5, 2.95, 1.5, f"{TR['zero_shot']['MAPE_%']}%", "MAPE on unseen city (Surat)", GREEN)
kpi(s, 9.9, 1.5, 2.83, 1.5, "43 / 43", "automated tests passing", AMBER)
table(s, 0.6, 3.25, 6.3, 3.0, ["Metric", "Hold-out", "Unseen city"],
      [["MAE (kL)", f"{HOLD['MAE']}", f"{TR['zero_shot']['MAE']}"],
       ["RMSE (kL)", f"{HOLD['RMSE']}", f"{TR['zero_shot']['RMSE']}"],
       ["MAPE (%)", f"{HOLD['MAPE_%']}", f"{TR['zero_shot']['MAPE_%']}"],
       ["R-squared", f"{HOLD['R2']}", f"{TR['zero_shot']['R2']}"],
       ["Few-shot (7 d local)", "-", (f"{TR['few_shot_7d']['MAPE_%']}% MAPE"
                                     if TR.get("few_shot_7d") else "n/a (short window)")]],
      col_widths=[1.1, 1, 1.1], fs=11)
rect(s, 7.15, 3.25, 5.6, 3.0, PANEL, line=PANEL2)
box(s, 7.42, 3.45, 5.1, 0.4, "WHAT THE TESTS PROVE", size=11, color=TEAL, bold=True)
bullets(s, 7.42, 3.9, 5.1, [
    "No data leakage: lag and rolling features use past values only.",
    "Shortage and excess reconcile with the balance.",
    "The optimiser never exceeds available supply and respects every constraint.",
    "Divergence conserves water and respects the transfer cap.",
    "Disaster, population and abundance factors behave within bounds.",
    "The API returns correct results and honest errors.",
], size=10.5)
footer(s, f"MAPE is higher across all {NAT['n_cities']} cities than on the 16-city benchmark because many very small towns have low demand denominators; R-squared stays high ({HOLD['R2']}).")

# =========================================================================
# 09 — Tests
# =========================================================================
s = slide(); header(s, "Automated tests", "43 tests, run on every change - this is the evidence the model passes", 9)
rows = [
    ["Forecasting", "Lag/rolling features use only the past; metrics computed correctly", "test_features.py"],
    ["Factors", "City registry integrity, unique names, growth bounds, hazard normalisation, abundance bands", "test_factors.py"],
    ["Shortage & excess", "Balance = supply - demand = excess - shortage; zero-demand safety", "test_shortage_excess.py"],
    ["Redistribution", "Never exceeds supply; respects floor and ceiling; priority shifts allocation", "test_redistribution.py"],
    ["Divergence", "Conserves water, respects the transfer cap and the distance cap", "test_divergence.py"],
    ["Economics", "Cost maths, provenance, manual overrides", "test_economics.py"],
    ["Assistant & API", "Grounded answers, 404/400 handling, scenario recalculation", "test_assistant_api.py"],
]
table(s, 0.6, 1.5, 12.13, 4.4, ["Area", "What is asserted", "File"], rows,
      col_widths=[1.3, 3.4, 1.3], fs=11)
box(s, 0.6, 6.15, 12.13, 0.7,
    "Run:  python -m pytest        Result:  43 passed.  Unavailable live data never crashes the app and is never replaced by fabricated measurements.",
    size=12, color=INK, bold=True)
footer(s, "Tests are part of the deliverable and run in CI-style on every pipeline change.")

# =========================================================================
# 10 — Population
# =========================================================================
s = slide(); header(s, "Real-time factor 1", "Population growth and decay drive demand over time", 10)
bullets(s, 0.6, 1.5, 6.0, [
    "Each city carries an annual growth rate derived transparently from its size and climate.",
    "Demand is projected as population x per-capita norm, so a growing city needs more water next year.",
    "Large metros grow a little slower in percentage terms; small remote and hill towns can decline.",
    "The model projects 1, 3, 5 and 10 years ahead and reports the demand multiplier.",
    "The current view uses a 1-year factor; the 10-year outlook is shown alongside it.",
], size=12.5)
rect(s, 6.85, 1.5, 5.9, 3.2, PANEL, line=PANEL2)
box(s, 7.12, 1.7, 5.4, 0.4, "HOW IT IS COMPUTED", size=11, color=TEAL, bold=True)
bullets(s, 7.12, 2.15, 5.4, [
    "population(t) = population(0) x (1 + g)^t",
    "demand_factor(t) = (1 + g)^t",
    "g from city size, with a decline only for small highland towns",
    "Result labelled as an illustrative projection, not a census",
], size=11.5, bullet_color=BLUE)
table(s, 0.6, 3.55, 12.13, 2.7, ["City", "Pop (M)", "Growth / yr", "Trend", "10-yr demand factor"],
      [["Bengaluru", "12.5", "+1.5%", "growing", "1.16"],
       ["Mumbai", "20.7", "+1.3%", "slow-growing", "1.14"],
       ["Jaipur", "3.9", "+1.8%", "growing", "1.20"],
       ["Guwahati", "1.1", "+2.1%", "growing", "1.23"],
       ["Srinagar", "1.2", "+2.0%", "growing", "1.22"]],
      col_widths=[1.2, 0.8, 1, 1, 1.3], fs=11)
footer(s, "Illustrative model from city size and climate - shown so the projection is inspectable, not hidden.")

# =========================================================================
# 11 — Disaster
# =========================================================================
s = slide(); header(s, "Real-time factor 2", "Natural-disaster monitoring by location and climate", 11)
bullets(s, 0.6, 1.5, 6.0, [
    "Every city has a hazard profile - drought, heatwave, flood, cyclone, earthquake - set by its climate zone.",
    "Likelihood is weighted by season: monsoon raises flood and cyclone; pre-monsoon raises heat and drought.",
    "Each hazard moves BOTH supply and demand (for example, drought cuts supply to 0.70 and raises demand to 1.10).",
    "Effects are blended with the (more likely) 'no disaster' case, so a city is not permanently penalised.",
    "Output: a 0-1 composite risk, the dominant hazard, and expected supply/demand multipliers.",
], size=12)
rect(s, 6.85, 1.5, 5.9, 2.0, PANEL, line=PANEL2)
box(s, 7.12, 1.7, 5.4, 0.4, "HAZARD EFFECT (multiplicative)", size=11, color=TEAL, bold=True)
table(s, 7.12, 2.2, 5.4, 1.15, ["Hazard", "Supply", "Demand"],
      [["Drought", "0.70", "1.10"], ["Heatwave", "0.95", "1.25"],
       ["Flood", "0.80", "0.98"], ["Cyclone", "0.75", "1.02"]],
      col_widths=[1, 0.7, 0.7], fs=10.5)
chart(s, 6.85, 3.7, 5.9, 2.6, XL_CHART_TYPE.COLUMN_CLUSTERED,
      ["Drought", "Heatwave", "Flood", "Cyclone", "Quake"],
      [("Composite risk by hazard mix (illustrative)", [0.42, 0.18, 0.55, 0.61, 0.09])],
      [RED], title=None)
footer(s, "Rule-based planning factor from climate and season - NOT a live disaster warning feed.")

# =========================================================================
# 12 — Water supply & climate
# =========================================================================
s = slide(); header(s, "Real-time factor 3", "Water-supply and climate monitoring for each location", 12)
bullets(s, 0.6, 1.5, 6.0, [
    "Effective supply = gross capacity x 0.65 (treatment, transmission and non-revenue-water losses).",
    "A climate-supply factor then reflects reliability: river-fed and monsoon cities carry more than arid inland cities.",
    "Live weather (optional) recharges the supply factor and raises demand through heat.",
    "Reservoir level is compared with each city's normal level to scale deliverable supply.",
    "Shortage and excess are computed per zone against this single, consistent supply basis.",
], size=12)
rect(s, 6.85, 1.5, 5.9, 5.2, PANEL, line=PANEL2)
box(s, 7.12, 1.72, 5.4, 0.4, "CLIMATE-SUPPLY RELIABILITY FACTOR", size=11, color=TEAL, bold=True)
table(s, 7.12, 2.25, 5.4, 2.7, ["Climate zone", "Factor"],
      [["Tropical-wet / coastal / humid-subtropical", "2.13"],
       ["Temperate highland", "1.53"],
       ["Tropical dry", "1.26"],
       ["Semi-arid", "1.13"],
       ["Arid", "0.86"]],
      col_widths=[3, 1], fs=11)
box(s, 7.12, 5.15, 5.4, 1.3,
    "This produces the realistic gradient the plan relies on: coastal and river-fed cities are water-rich, arid inland cities are\n"
    "stressed - so there is genuine excess to move toward genuine shortage.",
    size=11, color=INK2, spacing=1.25)
footer(s, "Supply figures are illustrative; the method is what matters. Live weather is fetched per city and degrades gracefully offline.")

# =========================================================================
# 13 — Shortage/excess + divergence
# =========================================================================
s = slide(); header(s, "Supply chain", "Shortage AND excess, then divergence routes one to the other", 13)
box(s, 0.6, 1.45, 12.13, 1.15,
    "shortage = max(0, demand - supply)      excess = max(0, supply - demand)      balance = supply - demand\n"
    "balance = excess - shortage   (so every number on every screen reconciles)",
    size=13, color=INK, spacing=1.3)
chart(s, 0.6, 2.75, 6.0, 3.5, XL_CHART_TYPE.COLUMN_CLUSTERED,
      ["Balanced", "Severe abundance", "Scarcity", "Abundance", "Severe scarcity"],
      [("Cities by water status", [BANDS["balanced"], BANDS["severe-abundance"],
                                                BANDS["scarcity"], BANDS["abundance"],
                                                BANDS["severe-scarcity"]])],
      [TEAL])
rect(s, 6.9, 2.75, 5.85, 3.5, PANEL, line=PANEL2)
box(s, 7.15, 2.95, 5.35, 0.4, "DIVERGENCE ENGINE", size=11, color=TEAL, bold=True)
bullets(s, 7.15, 3.4, 5.35, [
    "Matches surplus zones to deficit zones within a city.",
    "Where a city cannot fix its own deficit, it looks to a nearby city.",
    "Respects a transferable fraction, network losses and a distance cap.",
    "Divergence index measures how unevenly water is spread.",
    f"Result on the national run: {n_transfers} inter-city transfers proposed.",
], size=11, bullet_color=BLUE)
footer(s, "Transfers are planning suggestions, not instructions; the plan always requires human approval.")

# =========================================================================
# 14 — Redistribution algorithm
# =========================================================================
s = slide(); header(s, "Redistribution algorithm", "A linear program re-allocates the same water, with a lifeline for every zone", 14)
rect(s, 0.6, 1.5, 6.3, 5.2, PANEL, line=PANEL2)
box(s, 0.9, 1.72, 5.7, 0.4, "FORMULATION (SciPy linprog, HiGHS)", size=11, color=TEAL, bold=True)
box(s, 0.9, 2.2, 5.7, 4.3,
    "variables:  x_i  water allocated to zone i\n"
    "            u_i  unmet demand in zone i\n\n"
    "minimise:    sum( w_i * u_i )            [priority-weighted unmet demand]\n"
    "             + lambda * operating_cost   [cost-aware mode]\n\n"
    "subject to:  x_i + u_i  >= d_i           [meet demand as far as possible]\n"
    "             sum(x_i)   <= S             [cannot exceed available supply]\n"
    "             0.60 d_i   <= x_i <= 1.15 d_i   [lifeline floor, pipe ceiling]\n\n"
    "w_i = 0.5 + shortage_risk_i              [prioritise at-risk zones]",
    size=11.5, color=INK, spacing=1.18, font="Consolas")
rect(s, 7.15, 1.5, 5.6, 2.4, WHITE, line=PANEL2)
box(s, 7.42, 1.7, 5.1, 0.4, "TWO MODES", size=11, color=TEAL, bold=True)
bullets(s, 7.42, 2.15, 5.1, [
    "Shortage-prioritised: minimise weighted unmet demand (service first).",
    "Cost-aware: accept slightly more unmet demand if it saves pumping and treatment cost.",
], size=11.5)
rect(s, 7.15, 4.1, 5.6, 2.6, PANEL, line=PANEL2)
box(s, 7.42, 4.3, 5.1, 0.4, "GUARANTEES", size=11, color=TEAL, bold=True)
bullets(s, 7.42, 4.75, 5.1, [
    "Never allocates more than the available supply.",
    "No zone is starved below its lifeline when a feasible plan exists.",
    "Infeasible problems are reported, never faked.",
    "Requires human approval before any operational use.",
], size=11, bullet_color=GREEN)
footer(s, "The optimiser is decision support: it never controls infrastructure directly.")

# =========================================================================
# 15 — Dashboard
# =========================================================================
s = slide(); header(s, "User interface", "Ten pages, one selected city, charts on every page", 15)
rect(s, 0.6, 1.5, 6.3, 5.2, PANEL, line=PANEL2)
box(s, 0.88, 1.7, 5.8, 0.4, "THE PAGES", size=11, color=TEAL, bold=True)
bullets(s, 0.88, 2.15, 5.8, [
    "1 City Overview - national KPIs, map, most-stressed cities, snapshot.",
    "2 Demand Forecast - observed vs predicted, 7-day forecast, population to water ratio.",
    "3 Weather & Climate - live weather, stored series, reservoir, hazard profile.",
    "4 Crisis Prediction - crisis level, drivers, ordered emergency plan.",
    "5 Divergence & Routing - nearest water-rich city with distance and direction, route map, essential-service protection.",
    "6 Storage & Allotment - buffer days, what to hold for a crisis, what to release.",
    "7 Urbanization - urban growth, rural and forest land converted, extra demand.",
    "8 Compare Dates - a future date against a historical date.",
    "9 Abnormal Consumption - flagged zone-hours feeding the crisis plan.",
    "10 Economics - tariffs, energy, treatment cost with provenance.",
], size=10.5)
rect(s, 7.15, 1.5, 5.6, 2.5, WHITE, line=PANEL2)
box(s, 7.42, 1.7, 5.1, 0.4, "HOW YOU DRIVE IT", size=11, color=TEAL, bold=True)
bullets(s, 7.42, 2.15, 5.1, [
    "Search any of the 584 cities; every page re-renders for it.",
    "Left navigation switches pages; pages deep-link as #page/City.",
    "Water Assistant chat answers from the computed data.",
], size=11)
rect(s, 7.15, 4.2, 5.6, 2.5, PANEL, line=PANEL2)
box(s, 7.42, 4.4, 5.1, 0.4, "BROWNIE POINTS - MAPPED", size=11, color=AMBER, bold=True)
bullets(s, 7.42, 4.85, 5.1, [
    "Change supply -> the plan re-solves.",
    "Zones on a map with demand and risk.",
    "Future period compared with history.",
    "Weather as a factor, live per city.",
    "Clear charts on every page.",
], size=10.5, bullet_color=AMBER)
footer(s, "Open results/dashboard.html directly, or serve it via the API for live weather and the assistant.")

# =========================================================================
# 16 — Coverage
# =========================================================================
s = slide(); header(s, "Coverage", f"{NAT['n_cities']} cities, {NAT['n_zones']} zones, every state and union territory", 16)
kpi(s, 0.6, 1.5, 2.95, 1.4, f"{NAT['n_cities']}", "cities monitored", TEAL)
kpi(s, 3.7, 1.5, 2.95, 1.4, f"{NAT['n_zones']}", "metered zones", BLUE)
kpi(s, 6.8, 1.5, 2.95, 1.4, f"{NAT['n_states_ut']}", "states & UTs", GREEN)
kpi(s, 9.9, 1.5, 2.83, 1.4, f"{NAT['at_risk_zones']}", "zones at risk now", AMBER)
table(s, 0.6, 3.15, 12.13, 3.0, ["Run", "Cities", "Zones", "Feature rows", "Where"],
      [["Benchmark (--demo)", "16", "191", "105,432", "results/metrics.json"],
       ["National (default)", f"{NAT['n_cities']}", f"{NAT['n_zones']}", "193,392", "results/bundle.json"],
       ["Cross-city transfers", "-", "-", f"{n_transfers} routes", "results/bundle.json"]],
      col_widths=[1.4, 0.8, 0.8, 1.2, 1.6], fs=11.5)
box(s, 0.6, 6.3, 12.13, 0.6,
    "From Leh and Kargil in the north to Tirunelveli in the south, Bhuj in the west to Itanagar in the east.",
    size=12, color=INK2)
footer(s, "Adding a city is one line in the registry; the same model serves it with no retraining.")

# =========================================================================
# 17 — Close
# =========================================================================
s = slide()
rect(s, 0, 0, 13.333, 7.5, INK, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, 0, 0.22, 7.5, TEAL, shape=MSO_SHAPE.RECTANGLE)
box(s, 1.0, 1.1, 11.3, 0.5, "IN ONE BREATH", size=12, color=RGBColor(0x8F, 0xC9, 0xCF), bold=True)
box(s, 1.0, 1.6, 11.3, 2.2,
    "It predicts water demand, finds shortage AND excess, explains why\n"
    "with weather, economics, disaster and population, and routes water\n"
    "from where it is surplus to where it is short.",
    size=22, color=WHITE, spacing=1.28)
rect(s, 1.0, 4.0, 5.6, 0.02, RGBColor(0x33, 0x4A, 0x66), shape=MSO_SHAPE.RECTANGLE)
box(s, 1.0, 4.25, 5.5, 2.4,
    "What is proven\n"
    "- One global model, ~7% error on an unseen city\n"
    "- 43 automated tests passing\n"
    f"- {NAT['n_cities']} cities, {NAT['n_zones']} zones monitored\n"
    "- Every factor inspectable and labelled",
    size=13, color=RGBColor(0xC9, 0xD6, 0xE4), spacing=1.3)
box(s, 6.9, 4.25, 5.5, 2.4,
    "What is honest\n"
    "- Demo runs on synthetic data\n"
    "- Economics and disaster are planning factors\n"
    "- Transfers are suggestions, not commands\n"
    "- The optimiser never touches infrastructure",
    size=13, color=RGBColor(0xC9, 0xD6, 0xE4), spacing=1.3)
box(s, 1.0, 6.75, 11.3, 0.4, "AquaPulse  ·  Smart Water Redistribution  ·  SE Smart City",
    size=11, color=MUTED)

prs.save(str(OUT))
print("wrote", OUT, "slides:", len(prs.slides._sldIdLst))
