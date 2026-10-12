"""Builds the self-contained multi-page dashboard from the pipeline bundle.

Pages (left navigation; the selected city applies to every page):
  1 Overview       national KPIs, map, city snapshot
  2 Forecast       demand history vs forecast, population -> water ratio
  3 Weather        live weather + forecast, climate, reservoir, hazards
  4 Crisis         crisis prediction, drivers, emergency plan
  5 Divergence     within-city moves + nearest abundant city (distance/route)
  6 Storage        reservoir storage, reserve vs release, future allotment
  7 Urbanization   urban growth, rural/forest conversion, future demand
  8 Compare        a future date vs a historical date
  9 Anomalies      abnormal consumption, linked to the crisis plan
 10 Economics      tariffs, energy, treatment cost, with provenance

Chart.js is inlined so the file works offline; the map uses Leaflet from a CDN
and degrades to a message if the CDN is unreachable.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
CHARTJS = _HERE / "static" / "vendor" / "chart.umd.min.js"


def build_dashboard(bundle: dict, out_path: Path) -> Path:
    chart_js = ""
    if CHARTJS.exists():
        chart_js = CHARTJS.read_text(encoding="utf-8").replace("</script>", "<\\/script>")
    html = (_TEMPLATE
            .replace("/*__CHARTJS__*/", chart_js)
            .replace("__BUNDLE__", json.dumps(bundle, separators=(",", ":"))))
    # Explicit UTF-8: the dashboard contains non-ASCII glyphs (arrows, middots)
    # and Windows defaults to cp1252, which cannot encode them.
    Path(out_path).write_text(html, encoding="utf-8")
    return out_path


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>AquaPulse — Smart Water Redistribution</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>/*__CHARTJS__*/</script>
<style>
  :root{--bg:#0b1220;--panel:#131c2f;--panel2:#0f1728;--ink:#e9eefb;--muted:#93a3c4;
        --line:#22304d;--good:#2ecc71;--warn:#f5a623;--bad:#e74c3c;--accent:#39a0ed;
        --teal:#0e7c86}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 "Segoe UI",Roboto,system-ui,sans-serif}
  header{position:sticky;top:0;z-index:30;background:#0a101c;border-bottom:1px solid var(--line);
         padding:10px 18px;display:flex;gap:14px;flex-wrap:wrap;align-items:center}
  h1{font-size:16px;margin:0}
  .sub{color:var(--muted);font-size:11.5px}
  .kpis{display:flex;gap:8px;flex-wrap:wrap;margin-left:auto}
  .kpi{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:5px 11px}
  .kpi b{font-size:14px}.kpi span{color:var(--muted);font-size:10.5px;display:block}
  .picker{display:flex;gap:8px;align-items:center}
  input[type=text],input[type=date],select{background:var(--panel2);border:1px solid var(--line);
        color:var(--ink);border-radius:8px;padding:7px 10px;font-size:12.5px}
  #cityInput{width:230px}
  #layout{display:flex;height:calc(100vh - 62px)}
  nav{width:190px;flex:0 0 190px;background:#0d1524;border-right:1px solid var(--line);
      padding:10px 8px;overflow-y:auto}
  nav button{display:block;width:100%;text-align:left;background:transparent;border:0;color:var(--muted);
      padding:9px 11px;border-radius:8px;cursor:pointer;font-size:12.5px;margin-bottom:2px}
  nav button:hover{background:#131f33;color:var(--ink)}
  nav button.active{background:var(--accent);color:#fff;font-weight:600}
  main{flex:1;min-width:0;overflow-y:auto;padding:16px 18px 60px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:14px}
  .card h3{margin:0 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:#cfe0ff}
  .grid{display:grid;gap:12px}
  .g2{grid-template-columns:repeat(auto-fit,minmax(330px,1fr))}
  .g3{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
  .g4{grid-template-columns:repeat(auto-fit,minmax(175px,1fr))}
  .stat{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
  .stat .v{font-size:19px;font-weight:700}.stat .l{color:var(--muted);font-size:10.5px}
  .row{display:flex;justify-content:space-between;gap:8px;padding:3px 0;border-bottom:1px dashed #1c2740}
  .row:last-child{border-bottom:none}.row .k{color:var(--muted)}
  table{width:100%;border-collapse:collapse;font-size:12px}
  th,td{padding:5px 6px;border-bottom:1px solid #1a2438;text-align:right}
  th:first-child,td:first-child{text-align:left}
  th{color:var(--muted);font-weight:600;font-size:11px}
  .pill{padding:1px 7px;border-radius:9px;font-size:10.5px;font-weight:700;color:#fff}
  .band{padding:2px 9px;border-radius:999px;font-size:11px;font-weight:700}
  .b-severe-abundance{background:rgba(46,204,113,.18);color:#7fe0a5}
  .b-abundance{background:rgba(46,204,113,.12);color:#9fe6b8}
  .b-balanced{background:rgba(147,163,196,.18);color:#c3cfe6}
  .b-scarcity{background:rgba(245,166,35,.18);color:#ffcf7a}
  .b-severe-scarcity{background:rgba(231,76,60,.22);color:#ff9d8f}
  .lvl{font-weight:800;letter-spacing:.4px}
  .lvl-stable{color:#7fe0a5}.lvl-watch{color:#ffd88a}
  .lvl-warning{color:#ffb27a}.lvl-emergency{color:#ff8f80}
  canvas{max-height:280px}
  .mapbox{height:430px;border-radius:12px;overflow:hidden;border:1px solid var(--line)}
  .note{color:var(--muted);font-size:11px;margin-top:8px}
  .flex{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end}
  button.go{background:var(--accent);border:0;color:#fff;border-radius:8px;padding:8px 13px;cursor:pointer;font-weight:600}
  button.ghost{background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:8px;padding:6px 10px;cursor:pointer;font-size:11.5px}
  ul.plan{margin:0;padding-left:18px}ul.plan li{margin:4px 0}
  #chat{display:flex;flex-direction:column;gap:6px}
  #chatlog{max-height:170px;overflow-y:auto;background:var(--panel2);border:1px solid var(--line);
           border-radius:9px;padding:8px;font-size:12.5px}
  .msg{margin:4px 0}.msg.u{color:#9fd0ff}
</style>
</head>
<body>
<header>
  <div><h1>AquaPulse — Smart Water Redistribution</h1>
    <div class="sub">one model for every city · weather · economics · disaster · population · storage · urbanization</div></div>
  <div class="picker">
    <input id="cityInput" list="cityList" placeholder="search a city…" autocomplete="off"/>
    <datalist id="cityList"></datalist>
    <button class="ghost" id="prevCity">◀</button>
    <button class="ghost" id="nextCity">▶</button>
  </div>
  <div class="kpis" id="natKpis"></div>
</header>
<div id="layout">
  <nav id="nav"></nav>
  <main id="main"></main>
</div>
<script>
const B = __BUNDLE__;
const $ = s => document.querySelector(s);
const fmt = (n,d=0) => (n===null||n===undefined||isNaN(n))?"—":Number(n).toLocaleString("en-IN",{maximumFractionDigits:d});
const bandCls = b => "band b-"+b;
const riskColor = r => r>0.5?"#d73027":r>0.3?"#fc8d59":r>0.15?"#fee08b":r>0.05?"#91cf60":"#1a9850";
const bandColor = b => ({"severe-abundance":"#2ecc71","abundance":"#7fe0a5","balanced":"#93a3c4",
                          "scarcity":"#f5a623","severe-scarcity":"#e74c3c"})[b]||"#93a3c4";
const PAGES = [["overview","1 · City Overview"],["forecast","2 · Demand Forecast"],
  ["weather","3 · Weather & Climate"],["crisis","4 · Crisis Prediction"],
  ["divergence","5 · Divergence & Routing"],["storage","6 · Storage & Allotment"],
  ["urbanization","7 · Urbanization"],["compare","8 · Compare Dates"],
  ["anomalies","9 · Abnormal Consumption"],["economics","10 · Economics"]];

let cityName = B.meta.target_city, page = "overview";
/* deep links:  #page/CityName  (also lets the page be screenshotted/bookmarked) */
(function(){ const h=decodeURIComponent(location.hash.replace("#","")).split("/");
  if(h[0] && PAGES.some(p=>p[0]===h[0])) page=h[0];
  if(h[1]){ const m=B.cities.find(c=>c.city.toLowerCase()===h[1].toLowerCase()); if(m) cityName=m.city; } })();
function setHash(){ location.hash = page + "/" + encodeURIComponent(cityName); }
const city = () => B.cities.find(c => c.city === cityName) || B.cities[0];
const charts = {};
function draw(id, cfg){ const el=document.getElementById(id); if(!el) return;
  if(charts[id]) charts[id].destroy();
  charts[id]=new Chart(el, cfg); }
const baseOpts = {responsive:true, maintainAspectRatio:false, animation:false,
  plugins:{legend:{labels:{color:"#93a3c4",boxWidth:12,font:{size:10}}}},
  scales:{x:{ticks:{color:"#93a3c4",font:{size:10}},grid:{color:"#1a2740"}},
          y:{ticks:{color:"#93a3c4",font:{size:10}},grid:{color:"#1a2740"}}}};

/* ---------- header ---------- */
$("#cityList").innerHTML = B.cities.map(c=>`<option value="${c.city}">${c.state_ut}</option>`).join("");
$("#natKpis").innerHTML = [["Cities",B.national.n_cities],["Zones",B.national.n_zones],
  ["In crisis",B.national.cities_in_crisis],["Zones at risk",B.national.at_risk_zones],
  ["National shortage",fmt(B.national.total_shortage_kl)+" kL/d"],
  ["Transfers",(B.national.cross_city_transfers.transfers||[]).length]]
  .map(([l,v])=>`<div class="kpi"><b>${v}</b><span>${l}</span></div>`).join("");
$("#cityInput").value = cityName;
$("#cityInput").addEventListener("change", e=>{ const v=e.target.value.trim();
  const m=B.cities.find(c=>c.city.toLowerCase()===v.toLowerCase());
  if(m){ cityName=m.city; setHash(); renderAll(); } else { e.target.value=cityName; } });
$("#prevCity").onclick = ()=>{ let i=B.cities.findIndex(c=>c.city===cityName);
  cityName=B.cities[(i-1+B.cities.length)%B.cities.length].city; $("#cityInput").value=cityName; renderAll(); };
$("#nextCity").onclick = ()=>{ let i=B.cities.findIndex(c=>c.city===cityName);
  cityName=B.cities[(i+1)%B.cities.length].city; $("#cityInput").value=cityName; renderAll(); };

/* ---------- nav ---------- */
$("#nav").innerHTML = PAGES.map(([id,label])=>`<button data-p="${id}">${label}</button>`).join("");
document.querySelectorAll("#nav button").forEach(b=>b.onclick=()=>{ page=b.dataset.p; setHash(); renderAll(); });

function stat(v,l,color){ return `<div class="stat"><div class="v" style="color:${color||"#e9eefb"}">${v}</div><div class="l">${l}</div></div>`; }
function table(head, rows){ return `<table><thead><tr>${head.map(h=>`<th>${h}</th>`).join("")}</tr></thead><tbody>`+
  rows.map(r=>`<tr>${r.map(c=>`<td>${c??"—"}</td>`).join("")}</tr>`).join("")+`</tbody></table>`; }

/* ================= PAGES ================= */
function pageOverview(){
  const c=city();
  $("#main").innerHTML = `
    <div class="grid g4" id="ovKpis"></div>
    <div class="card"><h3>National map — every city coloured by shortage risk</h3>
      <div id="map1" class="mapbox"></div>
      <div class="note">Click a marker to select that city. Zone dots belong to the selected city.</div></div>
    <div class="grid g2">
      <div class="card"><h3>Most stressed cities</h3><div id="worst"></div></div>
      <div class="card"><h3>${c.city} snapshot</h3><div id="snap"></div></div>
    </div>`;
  $("#ovKpis").innerHTML =
    stat(fmt(c.shortage.total_demand_kl)+" kL/d","forecast demand", "#39a0ed")+
    stat(fmt(c.shortage.total_supply_kl)+" kL/d","effective supply")+
    stat(fmt(c.shortage.total_shortage_kl)+" kL/d","shortage","#ff9d8f")+
    stat(fmt(c.shortage.total_excess_kl)+" kL/d","excess","#9fe6b8")+
    stat(`<span class="lvl lvl-${c.crisis.level}">${c.crisis.level.toUpperCase()}</span>`,`crisis · score ${c.crisis.score}`)+
    stat(c.zones.filter(z=>z.at_risk).length+"/"+c.zones.length,"zones at risk");
  const worst=B.cities.slice().sort((a,b)=>b.shortage.worst_zone_risk-a.shortage.worst_zone_risk).slice(0,10);
  $("#worst").innerHTML = table(["City","Risk","Crisis","Band","Nearest donor"],
    worst.map(x=>[x.city,(x.shortage.worst_zone_risk*100).toFixed(1)+"%",
      `<span class="lvl lvl-${x.crisis.level}">${x.crisis.level}</span>`,
      `<span class="${bandCls(x.abundance.band)}">${x.abundance.band}</span>`,
      (x.nearest_donors&&x.nearest_donors[0])?`${x.nearest_donors[0].city} (${x.nearest_donors[0].distance_km} km ${x.nearest_donors[0].direction})`:"—"]));
  $("#snap").innerHTML =
    `<div class="row"><span class="k">State / UT</span><span>${c.state_ut}</span></div>
     <div class="row"><span class="k">Climate</span><span>${c.climate_zone}</span></div>
     <div class="row"><span class="k">Population</span><span>${c.pop_millions} M</span></div>
     <div class="row"><span class="k">Water status</span><span class="${bandCls(c.abundance.band)}">${c.abundance.band}</span></div>
     <div class="row"><span class="k">Per capita</span><span>${fmt(c.population_water.lpcd_now)} L/day (norm ${c.population_water.lpcd_norm})</span></div>
     <div class="row"><span class="k">Reservoir</span><span>${c.storage.reservoir_pct}% · buffer ${c.storage.days_of_buffer} days</span></div>
     <div class="row"><span class="k">Essential zones</span><span>${c.essential.essential_zones.length} of ${c.zones.length}</span></div>
     <div class="row"><span class="k">Coordinates</span><span>${c.coord_source}</span></div>`;
  drawMap("map1", true);
}

function pageForecast(){
  const c=city(), pw=c.population_water;
  $("#main").innerHTML = `
    <div class="grid g4">
      ${stat(fmt(c.shortage.total_demand_kl)+" kL/d","forecast demand","#39a0ed")}
      ${stat(fmt(pw.lpcd_now)+" L","per capita per day","#7fe0a5")}
      ${stat(pw.ratio_index+"%","of normative per-capita")}
      ${stat(c.population.trend+" "+ (c.population.annual_growth_pct>0?"+":"")+c.population.annual_growth_pct+"%","population trend")}
    </div>
    <div class="card"><h3>Observed vs predicted demand — daily</h3><canvas id="c_trend"></canvas>
      <div class="note">Observed comes from the series; predicted is the model's forecast.</div></div>
    <div class="grid g2">
      <div class="card"><h3>Next ${c.forecast_daily.length} days — illustrative forecast</h3><canvas id="c_fc"></canvas>
        <div class="note">Recent daily mean x weekday factor x population growth (an extrapolation, labelled as such).</div></div>
      <div class="card"><h3>Zone demand vs supply</h3><div id="zt"></div></div>
    </div>`;
  draw("c_trend",{type:"line",data:{labels:c.trend.map(t=>t.date.slice(5)),
    datasets:[{label:"Observed",data:c.trend.map(t=>t.observed),borderColor:"#39a0ed",pointRadius:0},
              {label:"Predicted",data:c.trend.map(t=>t.predicted),borderColor:"#2ecc71",pointRadius:0}]},options:baseOpts});
  draw("c_fc",{type:"bar",data:{labels:c.forecast_daily.map(f=>f.date.slice(5)),
    datasets:[{label:"Forecast kL/day",data:c.forecast_daily.map(f=>f.forecast_kl),backgroundColor:"#1b6ca8"}]},options:baseOpts});
  $("#zt").innerHTML = table(["Zone","Demand","Supply","Risk","Essential"],
    c.zones.slice(0,12).map(z=>[z.zone_id,fmt(z.pred_daily_kl),fmt(z.supply_kl),
      `<span class="pill" style="background:${riskColor(z.shortage_risk)}">${(z.shortage_risk*100).toFixed(0)}%</span>`,
      z.essential?"yes":"—"]));
}

function pageWeather(){
  const c=city(), w=c.weather, d=c.disaster;
  $("#main").innerHTML = `
    <div class="grid g2">
      <div class="card"><h3>Current weather <button class="ghost" id="wxBtn">get live</button></h3>
        <div id="wxBody"></div></div>
      <div class="card"><h3>Climate & hazard profile</h3>
        <div class="row"><span class="k">Climate zone</span><span>${c.climate_zone}</span></div>
        <div class="row"><span class="k">Dominant hazard</span><span>${d.dominant_hazard}</span></div>
        <div class="row"><span class="k">Composite disaster risk</span><span>${d.disaster_risk} / 1</span></div>
        <div class="row"><span class="k">Supply x demand effect</span><span>x${d.expected_supply_multiplier} · x${d.expected_demand_multiplier}</span></div>
        <canvas id="c_haz" style="margin-top:8px"></canvas></div>
    </div>
    <div class="grid g2">
      <div class="card"><h3>Stored weather series (last 10 days, historical)</h3><canvas id="c_wx"></canvas>
        <div class="note">Daily temperature and rainfall from the stored series. Live hourly values appear above when the API is reachable.</div></div>
      <div class="card"><h3>Reservoir level (last 10 days)</h3><canvas id="c_res"></canvas></div>
    </div>`;
  renderWeatherBox(w);
  $("#wxBtn").onclick = getLive;
  const hz=Object.entries(d.hazard_likelihood).sort((a,b)=>b[1]-a[1]);
  draw("c_haz",{type:"bar",data:{labels:hz.map(h=>h[0]),datasets:[{label:"likelihood",data:hz.map(h=>h[1]),backgroundColor:"#e74c3c"}]},options:baseOpts});
  const s=(c.history_daily||[]);
  draw("c_wx",{type:"line",data:{labels:s.map(x=>x.date.slice(5)),datasets:[
    {label:"temp °C",data:s.map(x=>x.temp_c),borderColor:"#f5a623",pointRadius:0,yAxisID:"y"},
    {label:"rain mm",data:s.map(x=>x.rain_mm),borderColor:"#39a0ed",pointRadius:0,yAxisID:"y1"}]},
    options:{...baseOpts,scales:{x:{ticks:{color:"#93a3c4",font:{size:9}},grid:{color:"#1a2740"}},
      y:{ticks:{color:"#f5a623",font:{size:9}},grid:{color:"#1a2740"}},
      y1:{position:"right",ticks:{color:"#39a0ed",font:{size:9}},grid:{drawOnChartArea:false}}}}});
  draw("c_res",{type:"line",data:{labels:c.history_daily.map(h=>h.date.slice(5)),
    datasets:[{label:"reservoir %",data:c.history_daily.map(h=>h.reservoir_pct),borderColor:"#0e7c86",fill:false}]},options:baseOpts});
}
function renderWeatherBox(w){
  $("#wxBody").innerHTML = `
    <div class="row"><span class="k">Status</span><span>${w.status}</span></div>
    <div class="row"><span class="k">Temperature</span><span>${fmt(w.temperature_c,1)} °C</span></div>
    <div class="row"><span class="k">Rainfall</span><span>${fmt(w.rainfall_mm,2)} mm</span></div>
    <div class="row"><span class="k">Humidity</span><span>${fmt(w.humidity_pct,0)} %</span></div>
    <div class="row"><span class="k">Source</span><span>${w.source}</span></div>
    <div class="note">${w.note||""} Observed ${w.observed_at||"—"}.</div>`;
}
async function getLive(){
  if(location.protocol==="file:"){ $("#wxBody").innerHTML += `<div class="note">Start the API (uvicorn api:app) to fetch live weather.</div>`; return; }
  $("#wxBody").innerHTML = "<div class='note'>fetching…</div>";
  try{ const r=await fetch(`/weather/${encodeURIComponent(cityName)}`); const w=await r.json();
    renderWeatherBox(w);
    const f=w.forecast||[];
    if(f.length){ const el=document.createElement("canvas"); el.id="c_live"; $("#wxBody").appendChild(el);
      draw("c_live",{type:"line",data:{labels:f.map(x=>x.time.slice(5,16)),
        datasets:[{label:"forecast temp °C",data:f.map(x=>x.temperature_c),borderColor:"#f5a623",pointRadius:0}]},options:baseOpts}); }
  }catch(e){ $("#wxBody").innerHTML=`<div class="note">Live weather unavailable: ${e.message}</div>`; }
}

function pageCrisis(){
  const c=city(), cr=c.crisis;
  $("#main").innerHTML = `
    <div class="grid g3">
      <div class="card"><h3>Crisis level</h3>
        <div class="lvl lvl-${cr.level}" style="font-size:26px">${cr.level.toUpperCase()}</div>
        <div class="note">score ${cr.score} · horizon ${cr.horizon_days} days</div>
        <canvas id="c_crisis" style="margin-top:10px"></canvas></div>
      <div class="card"><h3>Drivers</h3><canvas id="c_drivers"></canvas></div>
      <div class="card"><h3>Emergency plan</h3>
        <ul class="plan">${cr.plan.map(p=>`<li><b>${p.action}</b><div class="note">${p.detail}</div></li>`).join("")}</ul></div>
    </div>
    <div class="grid g2">
      <div class="card"><h3>Why — driver detail</h3><div id="dt"></div></div>
      <div class="card"><h3>Linked storage posture</h3>
        <div class="row"><span class="k">Reservoir</span><span>${c.storage.reservoir_pct}% (normal ${c.storage.baseline_pct}%)</span></div>
        <div class="row"><span class="k">Buffer</span><span>${c.storage.days_of_buffer} days</span></div>
        <div class="row"><span class="k">Posture</span><span>${c.storage.posture}</span></div>
        <div class="row"><span class="k">Releasable now</span><span>${fmt(c.storage.releasable_kl)} kL</span></div>
        <div class="row"><span class="k">Abnormal-consumption events</span><span>${c.anomalies.length}</span></div>
        <div class="note">${cr.note}</div></div>
    </div>`;
  draw("c_crisis",{type:"doughnut",data:{labels:["crisis score","head-room"],
    datasets:[{data:[cr.score, Math.max(0,1-cr.score)],backgroundColor:["#e74c3c","#1b2740"],borderWidth:0}]},
    options:{responsive:true,maintainAspectRatio:false,animation:false,cutout:"68%",
      plugins:{legend:{labels:{color:"#93a3c4",font:{size:10}}}}}});
  draw("c_drivers",{type:"bar",data:{labels:cr.drivers.map(d=>d.factor),
    datasets:[{label:"contribution",data:cr.drivers.map(d=>+(d.value*d.weight).toFixed(3)),backgroundColor:"#f5a623"}]},
    options:{...baseOpts,indexAxis:"y"}});
  $("#dt").innerHTML = table(["Driver","Value","Weight","Contribution"],
    cr.drivers.map(d=>[d.factor,d.value,d.weight,(d.value*d.weight).toFixed(3)]));
}

function pageDivergence(){
  const c=city(), dv=c.divergence, nd=c.nearest_donors||[];
  $("#main").innerHTML = `
    <div class="grid g4">
      ${stat(dv.divergence_index,"divergence index")}
      ${stat(fmt(dv.total_shortage_kl)+" kL/d","shortage in city","#ff9d8f")}
      ${stat(fmt(dv.delivered_kl)+" kL/d","delivered by internal moves","#9fe6b8")}
      ${stat(fmt(dv.residual_shortage_kl)+" kL/d","residual after moves","#ffd88a")}
    </div>
    <div class="card"><h3>Where to go — nearest city with an abundance of water</h3>
      <div id="nd"></div>
      <div class="note">Sorted by distance, so the first row is the nearest and shortest route. Distances are straight-line; direction is compass bearing.</div>
      <div id="map2" class="mapbox" style="height:340px;margin-top:10px"></div></div>
    <div class="grid g2">
      <div class="card"><h3>Within-city moves (excess → shortage)</h3><div id="wt"></div></div>
      <div class="card"><h3>Essential-service protection</h3>
        <div class="row"><span class="k">Hospitals</span><span>${c.essential.facilities.hospitals}</span></div>
        <div class="row"><span class="k">Emergency services</span><span>${c.essential.facilities.emergency}</span></div>
        <div class="row"><span class="k">Critical facilities</span><span>${c.essential.facilities.critical}</span></div>
        <div class="row"><span class="k">Protection floor</span><span>${fmt(c.essential.protection_floor_kl)} kL/day</span></div>
        <div class="row"><span class="k">Protected zones</span><span>${c.essential.essential_zones.join(", ")}</span></div>
        <div class="note">The floor is enforced as a hard constraint in the optimiser.</div></div>
    </div>
    <div class="card"><h3>Zone-level plan (current vs recommended)</h3><canvas id="c_alloc"></canvas></div>`;
  $("#nd").innerHTML = nd.length ? table(["Donor city","Distance","Direction","Water status","Surplus kL/d","Deliverable kL/d"],
    nd.map(d=>[d.city,d.distance_km+" km",d.direction,`<span class="${bandCls(d.band)}">${d.band}</span>`,
      fmt(d.surplus_kl),fmt(d.deliverable_kl)])) :
    `<div class="note">This city has no residual shortage — no donor is needed.</div>`;
  $("#wt").innerHTML = dv.transfers.length ? table(["From → To","Sent kL","Delivered kL","Loss kL"],
    dv.transfers.slice(0,12).map(t=>[`${t.from_zone} → ${t.to_zone}`,fmt(t.sent_kl),fmt(t.delivered_kl),fmt(t.loss_kl)])) :
    "<div class='note'>No internal transfer required.</div>";
  draw("c_alloc",{type:"bar",data:{labels:c.zones.map(z=>z.zone_id),datasets:[
    {label:"Current kL",data:c.zones.map(z=>z.supply_kl),backgroundColor:"#93a3c4"},
    {label:"Recommended kL",data:c.zones.map(z=>z.recommended_supply_kl),backgroundColor:"#2ecc71"},
    {label:"Demand kL",data:c.zones.map(z=>z.pred_daily_kl),backgroundColor:"rgba(57,160,237,.4)"}]},options:baseOpts});
  drawDivMap("map2", c, nd);
}

function pageStorage(){
  const c=city(), s=c.storage;
  $("#main").innerHTML = `
    <div class="grid g4">
      ${stat(s.reservoir_pct+"%","reservoir level", s.reservoir_pct<s.baseline_pct?"#ff9d8f":"#7fe0a5")}
      ${stat(s.days_of_buffer+" d","days of demand in store","#39a0ed")}
      ${stat(fmt(s.reserve_target_kl)+" kL","reserve target (${s.reserve_target_days} d)")}
      ${stat(s.posture.toUpperCase(),"posture","#ffd88a")}
    </div>
    <div class="grid g2">
      <div class="card"><h3>Stored vs capacity vs reserve target</h3><canvas id="c_store"></canvas>
        <div class="note">Capacity is illustrative: ${s.capacity_days_assumption} days of supply.</div></div>
      <div class="card"><h3>Allotment for a future crisis</h3>
        <div class="row"><span class="k">Stored now</span><span>${fmt(s.stored_kl)} kL</span></div>
        <div class="row"><span class="k">Reserve target</span><span>${fmt(s.reserve_target_kl)} kL</span></div>
        <div class="row"><span class="k">Reserve gap</span><span>${fmt(s.reserve_gap_kl)} kL</span></div>
        <div class="row"><span class="k">Releasable now</span><span>${fmt(s.releasable_kl)} kL</span></div>
        <div class="row"><span class="k">Essential reserve (7 d)</span><span>${fmt(s.essential_reserve_kl)} kL</span></div>
        <div class="note">${s.advice}</div></div>
    </div>`;
  draw("c_store",{type:"bar",data:{labels:["stored","reserve target","releasable"],
    datasets:[{label:"kL",data:[s.stored_kl,s.reserve_target_kl,s.releasable_kl],
      backgroundColor:["#0e7c86","#f5a623","#2ecc71"]}]},options:baseOpts});
}

function pageUrbanization(){
  const c=city(), u=c.urbanization;
  $("#main").innerHTML = `
    <div class="grid g4">
      ${stat((u.urban_share*100).toFixed(0)+"%","urban share")}
      ${stat(u.builtup_km2_now+" km²","built-up now")}
      ${stat("+"+u.land_converted_km2_10y+" km²","rural/forest converted in 10 y","#f5a623")}
      ${stat("+"+fmt(u.extra_demand_kl_10y)+" kL/d","extra demand in 10 y","#ff9d8f")}
    </div>
    <div class="card"><h3>Projection — urban population, built-up area and water demand</h3><canvas id="c_urb"></canvas>
      <div class="note">Density held at ${u.density_assumption} people/km². ${u.note}</div></div>
    <div class="grid g2">
      <div class="card"><h3>Growth table</h3><div id="ut"></div></div>
      <div class="card"><h3>Why this matters</h3>
        <div class="note">New built-up area appears on the urban fringe — land that is
        rural or forest today. Those households consume more water per head than they
        did before, so the extra demand above is what the city must reserve capacity
        for. Cities with the fastest growth and the largest converted area should be
        planned first.</div>
        <div class="row" style="margin-top:8px"><span class="k">Population trend</span><span>${c.population.trend} (${c.population.annual_growth_pct}%/yr)</span></div>
        <div class="row"><span class="k">10-year demand factor</span><span>x${c.population.ten_year_demand_factor}</span></div>
        <div class="row"><span class="k">20-year extra demand</span><span>${fmt(u.extra_demand_kl_20y)} kL/day</span></div></div>
    </div>`;
  draw("c_urb",{type:"line",data:{labels:u.projection.map(p=>"+"+p.years_ahead+"y"),datasets:[
    {label:"urban pop (M)",data:u.projection.map(p=>p.urban_pop_millions),borderColor:"#39a0ed",yAxisID:"y"},
    {label:"built-up km²",data:u.projection.map(p=>p.builtup_km2),borderColor:"#f5a623",yAxisID:"y1"}]},
    options:{...baseOpts,scales:{x:{ticks:{color:"#93a3c4"},grid:{color:"#1a2740"}},
      y:{ticks:{color:"#39a0ed"},grid:{color:"#1a2740"}},
      y1:{position:"right",ticks:{color:"#f5a623"},grid:{drawOnChartArea:false}}}}});
  $("#ut").innerHTML = table(["Horizon","Urban pop (M)","Built-up km²","Demand factor","Extra kL/d"],
    u.projection.map(p=>["+"+p.years_ahead+" y",p.urban_pop_millions,p.builtup_km2,"x"+p.demand_factor,fmt(p.extra_demand_kl)]));
}

let cmpHist=0, cmpFut=0;
function pageCompare(){
  const c=city();
  const H=c.history_daily, F=c.forecast_daily;
  cmpHist=Math.min(cmpHist,H.length-1); cmpFut=Math.min(cmpFut,F.length-1);
  $("#main").innerHTML = `
    <div class="card"><h3>Compare a future date with a historical date</h3>
      <div class="flex">
        <label class="sub">Historical day <select id="hsel">${H.map((h,i)=>`<option value="${i}" ${i===cmpHist?"selected":""}>${h.date}</option>`).join("")}</select></label>
        <label class="sub">Future day <select id="fsel">${F.map((f,i)=>`<option value="${i}" ${i===cmpFut?"selected":""}>${f.date}</option>`).join("")}</select></label>
      </div>
      <div class="grid g2" style="margin-top:12px">
        <div id="cmpt"></div><canvas id="c_cmp"></canvas></div>
      <div class="note">Historical values are observed from the series; the future day is the
      model's forecast for ${c.city}. Both are for the selected city.</div></div>`;
  const paint=()=>{
    const h=H[cmpHist], f=F[cmpFut];
    const demandNow=h.observed_kl, demandFut=f.forecast_kl;
    const dPct = demandNow>0 ? (100*(demandFut-demandNow)/demandNow) : 0;
    $("#cmpt").innerHTML = table(["Metric","Historical "+h.date,"Future "+f.date,"Change"],
      [["Demand kL/day",fmt(h.observed_kl),fmt(f.forecast_kl),(dPct>0?"+":"")+dPct.toFixed(1)+"%"],
       ["Temperature °C",h.temp_c,"—","—"],
       ["Rainfall mm",h.rain_mm,"—","—"],
       ["Reservoir %",h.reservoir_pct,"—","—"]]);
    draw("c_cmp",{type:"bar",data:{labels:["Historical","Future"],
      datasets:[{label:"Demand kL/day",data:[h.observed_kl,f.forecast_kl],
        backgroundColor:["#93a3c4","#39a0ed"]}]},options:baseOpts});
  };
  $("#hsel").onchange=e=>{cmpHist=+e.target.value; paint();};
  $("#fsel").onchange=e=>{cmpFut=+e.target.value; paint();};
  paint();
}

function pageAnomalies(){
  const c=city();
  $("#main").innerHTML = `
    <div class="grid g4">
      ${stat(c.anomalies.length,"flagged zone-hours","#f5a623")}
      ${stat(c.anomalies.filter(a=>a.direction==="up").length,"surges (up)","#ff9d8f")}
      ${stat(c.anomalies.filter(a=>a.direction==="down").length,"drops (down)")}
      ${stat(c.crisis.level.toUpperCase(),"feeds the crisis plan","#ffd88a")}
    </div>
    <div class="grid g2">
      <div class="card"><h3>Anomaly scores by zone</h3><canvas id="c_anom"></canvas></div>
      <div class="card"><h3>From anomaly to action</h3>
        <div class="note">Each flagged zone is fed into the crisis plan. Where a surge is
        confirmed as wastage, water is diverted to at-risk and essential zones instead.</div>
        <ul class="plan">${c.crisis.plan.filter(p=>/abnormal/i.test(p.action)).map(p=>`<li><b>${p.action}</b><div class="note">${p.detail}</div></li>`).join("") || "<li>No anomaly-driven action at this crisis level.</li>"}</ul></div>
    </div>
    <div class="card"><h3>Flagged zone-hours</h3><div id="at"></div></div>`;
  const agg={}; c.anomalies.forEach(a=>{ agg[a.zone_id]=Math.max(agg[a.zone_id]||0,a.score); });
  draw("c_anom",{type:"bar",data:{labels:Object.keys(agg),datasets:[{label:"peak score",data:Object.values(agg),backgroundColor:"#f5a623"}]},options:baseOpts});
  $("#at").innerHTML = table(["Zone","Time","Observed","Expected","z","Direction"],
    c.anomalies.slice(0,15).map(a=>[a.zone_id,a.time,fmt(a.observed_kl),fmt(a.expected_kl),a.z??"—",a.direction]));
}

function pageEconomics(){
  const c=city(), e=B.economics;
  $("#main").innerHTML = `
    <div class="card"><h3>Economic indicators (with source and provenance)</h3>
      ${table(["Variable","Value","Unit","Kind","Source"],
        e.variables.map(v=>[v.label,fmt(v.value,2),v.unit,v.kind,v.source]))}
      <div class="note">${e.note}</div></div>
    <div class="grid g2">
      <div class="card"><h3>Operating cost — ${c.city}</h3>
        <div class="row"><span class="k">Volume</span><span>${fmt(c.operating_cost.volume_kl)} kL/day</span></div>
        <div class="row"><span class="k">Energy</span><span>${fmt(c.operating_cost.energy_kwh)} kWh</span></div>
        <div class="row"><span class="k">Energy cost</span><span>INR ${fmt(c.operating_cost.energy_cost_inr)}</span></div>
        <div class="row"><span class="k">Treatment cost</span><span>INR ${fmt(c.operating_cost.treatment_cost_inr)}</span></div>
        <div class="row"><span class="k">Total</span><span>INR ${fmt(c.operating_cost.total_operating_cost_inr)}/day</span></div>
        <div class="row"><span class="k">Cost per kL</span><span>INR ${c.operating_cost.cost_per_kl_inr}</span></div>
        <div class="note">${c.operating_cost.caveat}</div></div>
      <div class="card"><h3>Cost of the two plans</h3>
        <div class="row"><span class="k">Shortage-prioritised unmet</span><span>${fmt(c.plan.optimised_unmet_kl)} kL</span></div>
        <div class="row"><span class="k">Cost-aware unmet</span><span>${fmt(c.plan_cost.optimised_unmet_kl)} kL</span></div>
        <div class="row"><span class="k">Essential floor</span><span>${fmt(c.plan.essential_floor_kl)} kL</span></div>
        <div class="note">A cheaper plan is not automatically better; both respect the essential-services floor.</div></div>
    </div>`;
}

/* ---------- maps ---------- */
let map1=null, map2=null, markers=[];
function drawMap(id, allCities){
  if(typeof L==="undefined"){ document.getElementById(id).innerHTML =
    "<div style='padding:16px;color:#93a3c4'>Map needs internet for tiles. Use the pages on the left.</div>"; return; }
  if(!map1){ map1=L.map(id).setView([22.5,79],5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap'}).addTo(map1); }
  markers.forEach(m=>map1.removeLayer(m)); markers=[];
  B.cities.forEach(c=>{
    const r=Math.max(4,Math.min(16,4+c.pop_millions*0.6));
    const m=L.circleMarker([c.lat,c.lon],{radius:r,color:'#111',weight:0.6,
        fillColor:riskColor(c.shortage.worst_zone_risk),fillOpacity:0.8})
      .bindPopup(`<b>${c.city}</b><br>${c.state_ut} · ${c.climate_zone}<br>
        ${c.abundance.band} (idx ${c.abundance.abundance_index})<br>
        crisis ${c.crisis.level}<br>shortage ${fmt(c.shortage.total_shortage_kl)} · excess ${fmt(c.shortage.total_excess_kl)} kL/d`)
      .on('click',()=>{cityName=c.city;$("#cityInput").value=c.city;renderAll();}).addTo(map1);
    markers.push(m);
  });
  const sel=city();
  sel.zones.forEach(z=>{ const m=L.circleMarker([z.lat,z.lon],{radius:5,color:'#000',weight:0.4,
      fillColor:riskColor(z.shortage_risk),fillOpacity:0.95})
      .bindPopup(`<b>${z.zone_id}</b><br>demand ${fmt(z.pred_daily_kl)} kL/d<br>risk ${(z.shortage_risk*100).toFixed(0)}%`).addTo(map1);
    markers.push(m); });
  map1.setView([sel.lat,sel.lon],7);
}
function drawDivMap(id, c, nd){
  if(typeof L==="undefined") return;
  if(map2){ map2.remove(); map2=null; }
  map2=L.map(id).setView([c.lat,c.lon],6);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap'}).addTo(map2);
  L.circleMarker([c.lat,c.lon],{radius:9,color:'#111',weight:1,fillColor:'#e74c3c',fillOpacity:0.9})
    .bindPopup(`<b>${c.city}</b> — needs water`).addTo(map2);
  nd.forEach(d=>{
    L.circleMarker([d.lat,d.lon],{radius:8,color:'#111',weight:1,fillColor:'#2ecc71',fillOpacity:0.9})
      .bindPopup(`<b>${d.city}</b> — surplus ${fmt(d.surplus_kl)} kL/d<br>${d.distance_km} km ${d.direction}`).addTo(map2);
    L.polyline([[c.lat,c.lon],[d.lat,d.lon]],{color:'#39a0ed',weight:2,dashArray:'6 5'}).addTo(map2);
  });
}

/* ---------- assistant (client-side, mirrors src/assistant.py) ---------- */
function has(q,a){ return a.some(k=>q.toLowerCase().includes(k)); }
function findCity(q){ return B.cities.find(c=>q.toLowerCase().includes(c.city.toLowerCase())); }
function answer(q){
  const c=findCity(q)||city();
  if(has(q,["help","what can you"])) return "Ask about: weather, shortage, excess, transfers/divergence, disaster, population, storage, urbanization, crisis, cost.";
  if(has(q,["worst","most at risk"])){ const t=B.cities.slice().sort((a,b)=>b.crisis.score-a.crisis.score).slice(0,3);
    return "Highest crisis scores:\n"+t.map((x,i)=>`${i+1}. ${x.city} — ${x.crisis.level} (${x.crisis.score})`).join("\n"); }
  if(has(q,["crisis"])) return `${c.city} crisis level: ${c.crisis.level} (score ${c.crisis.score}).\n`+c.crisis.plan.map(p=>`- ${p.action}: ${p.detail}`).join("\n");
  if(has(q,["storage","reserve","buffer"])) return `${c.city}: reservoir ${c.storage.reservoir_pct}% (normal ${c.storage.baseline_pct}%), buffer ${c.storage.days_of_buffer} days, posture ${c.storage.posture}. Releasable now ${fmt(c.storage.releasable_kl)} kL.`;
  if(has(q,["urban","growth","forest","rural"])) return `${c.city} urbanization: ${(c.urbanization.urban_share*100).toFixed(0)}% urban, built-up ${c.urbanization.builtup_km2_now} km², +${c.urbanization.land_converted_km2_10y} km² of rural/forest converted in 10 y, adding ${fmt(c.urbanization.extra_demand_kl_10y)} kL/day.`;
  if(has(q,["essential","hospital","emergency"])) return `${c.city} protects ${c.essential.facilities.hospitals} hospitals, ${c.essential.facilities.emergency} emergency and ${c.essential.facilities.critical} critical facilities — a floor of ${fmt(c.essential.protection_floor_kl)} kL/day.`;
  if(has(q,["donor","nearest","divergence","transfer","where"])) return (c.nearest_donors||[]).length? `${c.city} — nearest water-rich city: ${c.nearest_donors[0].city}, ${c.nearest_donors[0].distance_km} km ${c.nearest_donors[0].direction} (${c.nearest_donors[0].band}, ${fmt(c.nearest_donors[0].deliverable_kl)} kL/d deliverable).` : `${c.city} has no residual shortage — no donor needed.`;
  if(has(q,["weather"])) return c.weather.status==="live"? `${c.city}: ${c.weather.temperature_c}°C, rain ${c.weather.rainfall_mm}mm (${c.weather.source}).` : `Live weather for ${c.city} is unavailable; using its ${c.climate_zone} climate series.`;
  if(has(q,["shortage"])) return `${c.city}: shortage ${fmt(c.shortage.total_shortage_kl)} kL/day across ${c.shortage.zones_in_shortage} zones; worst-zone risk ${(c.shortage.worst_zone_risk*100).toFixed(1)}%.`;
  if(has(q,["population","per capita","lpcd"])) return `${c.city}: ${c.pop_millions} M people, ${fmt(c.population_water.lpcd_now)} L per capita per day (norm ${c.population_water.lpcd_norm}), ${c.population.trend} at ${c.population.annual_growth_pct}%/yr.`;
  return `${c.city}: demand ${fmt(c.shortage.total_demand_kl)}, supply ${fmt(c.shortage.total_supply_kl)} kL/day, status ${c.abundance.band}, crisis ${c.crisis.level}. Ask about crisis, storage, urbanization, divergence, weather, essential services or population.`;
}
function chatWidget(){
  return `<div class="card"><h3>Ask the Water Assistant</h3><div id="chat">
    <div id="chatlog"><div class="msg">Ask about crisis, storage, urbanization, the nearest donor, weather, essential services…</div></div>
    <div style="display:flex;gap:6px"><input id="chatinput" type="text" placeholder="e.g. where is the nearest water?" style="flex:1"/>
    <button class="go" id="chatgo">Ask</button></div></div></div>`;
}
function wireChat(){
  const go=$("#chatgo"); if(!go) return;
  const send=()=>{ const q=$("#chatinput").value.trim(); if(!q) return; $("#chatinput").value="";
    $("#chatlog").insertAdjacentHTML("beforeend",`<div class="msg u">${q}</div>`);
    $("#chatlog").insertAdjacentHTML("beforeend",`<div class="msg">${answer(q).replace(/\n/g,"<br>")}</div>`);
    $("#chatlog").scrollTop=$("#chatlog").scrollHeight; };
  go.onclick=send; $("#chatinput").onkeydown=e=>{ if(e.key==="Enter") send(); };
}

/* ---------- render ---------- */
const RENDER={overview:pageOverview,forecast:pageForecast,weather:pageWeather,crisis:pageCrisis,
  divergence:pageDivergence,storage:pageStorage,urbanization:pageUrbanization,
  compare:pageCompare,anomalies:pageAnomalies,economics:pageEconomics};
function renderAll(){
  document.querySelectorAll("#nav button").forEach(b=>b.classList.toggle("active",b.dataset.p===page));
  RENDER[page]();
  if(page!=="weather"){ $("#main").insertAdjacentHTML("beforeend", chatWidget()); wireChat(); }
  else { $("#main").insertAdjacentHTML("beforeend", chatWidget()); wireChat(); }
}
renderAll();
</script>
</body>
</html>
"""
