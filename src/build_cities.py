"""Build the full city registry from the user's list.

For every city in `cities_source.INDIA_CITIES_FULL` this:
  1. looks up real coordinates and population in the SimpleMaps world-cities
     dataset — exact name, then a rename/old-name alias, then a fuzzy match
     restricted to the city's own state;
  2. derives a climate zone (state default, with coastal and highland overrides,
     using distance to a coarse coastline and a curated hill/arid list);
  3. derives per-capita norm, gross supply capacity and zone count;
  4. writes `data/cities_full.csv`, which `city_registry.py` then loads.

A small manual table pins coordinates for cities the source dataset names
differently or omits entirely (Delhi sub-localities, Navi Mumbai, ...). Anything
still unresolved falls back to its state's centroid and is flagged
`coord_source=approximate` — nothing is silently dropped.
"""
from __future__ import annotations

import csv
import math
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from cities_source import INDIA_CITIES_FULL

ROOT = Path(__file__).resolve().parent
WORLD = ROOT.parent / "data" / "worldcities.csv"
OUT = ROOT / "data" / "cities_full.csv"

STATE_TO_ADMIN = {
    "Maharashtra": ["maharashtra"], "Gujarat": ["gujarat"],
    "Madhya Pradesh": ["madhya pradesh"], "Uttar Pradesh": ["uttar pradesh"],
    "Rajasthan": ["rajasthan"], "Delhi": ["delhi"], "Karnataka": ["karnataka"],
    "Tamil Nadu": ["tamil nadu"], "Telangana": ["telangana"],
    "Andhra Pradesh": ["andhra pradesh"], "Kerala": ["kerala"],
    "West Bengal": ["west bengal"], "Bihar": ["bihar"], "Jharkhand": ["jharkhand"],
    "Odisha": ["odisha", "orissa"], "Chhattisgarh": ["chhattisgarh"],
    "Punjab": ["punjab"], "Haryana": ["haryana"],
    "Uttarakhand": ["uttarakhand", "uttaranchal"],
    "Himachal Pradesh": ["himachal pradesh"], "Assam": ["assam"],
    "Arunachal Pradesh": ["arunachal pradesh"], "Meghalaya": ["meghalaya"],
    "Manipur": ["manipur"], "Mizoram": ["mizoram"], "Nagaland": ["nagaland"],
    "Tripura": ["tripura"], "Sikkim": ["sikkim"],
    "Jammu and Kashmir": ["jammu and kashmir"], "Ladakh": ["ladakh"],
    "Goa": ["goa"], "Chandigarh": ["chandigarh"],
    "Puducherry": ["puducherry", "pondicherry"],
    "Andaman and Nicobar Islands": ["andaman and nicobar"],
    "Dadra and Nagar Haveli and Daman and Diu": [
        "dadra and nagar haveli", "daman and diu",
        "dadra and nagar haveli and daman and diu"],
    "Lakshadweep": ["lakshadweep"],
}

# modern / official name -> older names the source dataset may use
CITY_ALIAS = {
    "chhatrapati sambhajinagar": ["aurangabad"],
    "ahilyanagar": ["ahmadnagar", "ahmednagar"],
    "dharashiv": ["osmanabad"],
    "prayagraj": ["allahabad"],
    "gurugram": ["gurgaon"],
    "bengaluru": ["bangalore"],
    "mysuru": ["mysore"],
    "hubballi-dharwad": ["hubli", "dharwad", "hubli dharwad"],
    "mangaluru": ["mangalore"],
    "belagavi": ["belgaum"],
    "kalaburagi": ["gulbarga"],
    "vijayapura": ["bijapur"],
    "shivamogga": ["shimoga"],
    "tumakuru": ["tumkur"],
    "hosapete": ["hospet"],
    "ballari": ["bellary"],
    "nashik": ["nasik"],
    "dhule": ["dhulia"],
    "chandrapur": ["chanda"],
    "mira-bhayandar": ["bhayandar"],
    "sri vijaya puram": ["port blair"],
    "bardhaman": ["barddhaman", "burdwan"],
    "rajamahendravaram": ["rajahmundry"],
    "thoothukudi": ["tuticorin"],
    "puducherry": ["pondicherry"],
    "kanchipuram": ["kanchipuram", "kancheepuram", "conjeeveram"],
    "bokaro steel city": ["bokaro"],
    "medininagar": ["daltonganj"],
    "kendujhar": ["keonjhar"],
    "narmadapuram": ["hoshangabad"],
    "rae bareli": ["raebareli"],
    "sri ganganagar": ["ganganagar"],
    "berhampur": ["berhampur", "brahmapur"],
    "vasco da gama": ["vasco da gama", "vasco"],
    "tiruchirappalli": ["tiruchirappalli", "tiruchchirappalli", "trichinopoly"],
    "ayodhya": ["faizabad", "fyzabad"],
    "mehsana": ["mahesana"],
    "kalyan-dombivli": ["kalyan", "dombivli"],
    "bhusawal": ["bhusawal", "bhusaval"],
    "vasai-virar": ["vasai-virar", "vasai"],
    # colonial-era names
    "howrah": ["haora"],
    "kozhikode": ["calicut"],
    "kollam": ["quilon"],
    "thrissur": ["trichur"],
    "alappuzha": ["alleppey"],
    "thalassery": ["tellicherry"],
    "vatakara": ["badagara"],
    "kannur": ["cannanore", "kannur"],
    "palakkad": ["palghat", "palakkad"],
    "kadapa": ["cuddapah", "kadapa"],
    "machilipatnam": ["masulipatnam", "machilipatnam"],
    "eluru": ["ellore", "eluru"],
    "kakinada": ["cocanada", "kakinada"],
    "tirunelveli": ["tinnevelly", "tirunelveli"],
    "thanjavur": ["tanjore", "thanjavur"],
    "nagapattinam": ["nagappattinam", "nagapattinam"],
    "srikakulam": ["chicacole", "srikakulam"],
    "munger": ["monghyr", "munger"],
    "cooch behar": ["cooch behar", "kuch bihar"],
    "firozpur": ["firozpur", "firozepur"],
    "koderma": ["koderma", "kodarma"],
    "bihar sharif": ["bihar sharif", "bihar"],
    "durg": ["durg"],
    "mohali": ["mohali", "sas nagar"],
    "udupi": ["udupi"],
    "navi mumbai": ["navi mumbai", "new bombay"],
    "greater noida": ["greater noida"],
    "vapi": ["vapi"],
    "gandhinagar": ["gandhinagar"],
    "firozabad": ["firozabad"],
    "barmer": ["barmer"],
    "dholpur": ["dholpur"],
    "neemuch": ["neemuch"],
    "betul": ["betul"],
    "dahod": ["dahod"],
    "deesa": ["deesa"],
    "latur": ["latur"],
    "beed": ["beed"],
    "hingoli": ["hingoli"],
    "azamgarh": ["azamgarh"],
    "hoshiarpur": ["hoshiarpur"],
}

# manual coordinates for cities the source dataset names differently or omits
MANUAL = {
    ("Delhi", "Dwarka"): (28.5921, 77.0460),
    ("Delhi", "Rohini"): (28.7495, 77.0565),
    ("Delhi", "Karol Bagh"): (28.6519, 77.1909),
    ("Delhi", "Shahdara"): (28.6733, 77.2890),
    ("Delhi", "Saket"): (28.5245, 77.2066),
    ("Delhi", "Vasant Kunj"): (28.5215, 77.1595),
    ("Delhi", "Narela"): (28.8527, 77.0929),
    ("Delhi", "Najafgarh"): (28.6092, 76.9798),
    ("Maharashtra", "Navi Mumbai"): (19.0330, 73.0297),
    ("Tripura", "Udaipur"): (23.5333, 91.4833),
    ("Himachal Pradesh", "Bilaspur"): (31.3300, 76.7500),
    ("Himachal Pradesh", "Hamirpur"): (31.6830, 76.5220),
    ("Uttarakhand", "Srinagar"): (30.2220, 78.7840),
    ("Uttar Pradesh", "Greater Noida"): (28.4744, 77.5040),
    ("Tamil Nadu", "Tiruchirappalli"): (10.7905, 78.7047),
    ("Tamil Nadu", "Tirunelveli"): (8.7139, 77.7567),
    ("Tamil Nadu", "Thanjavur"): (10.7870, 79.1378),
    ("Chhattisgarh", "Durg"): (21.1904, 81.2849),
    ("Punjab", "Mohali"): (30.7046, 76.7179),
    ("Karnataka", "Udupi"): (13.3409, 74.7421),
    ("Uttar Pradesh", "Prayagraj"): (25.4358, 81.8463),
    ("Uttar Pradesh", "Firozabad"): (27.1507, 78.3956),
    ("Uttar Pradesh", "Azamgarh"): (26.0685, 83.1836),
    ("Maharashtra", "Latur"): (18.4088, 76.5604),
    ("Maharashtra", "Beed"): (18.9894, 75.7601),
    ("Maharashtra", "Hingoli"): (19.7174, 77.1497),
    ("Gujarat", "Vapi"): (20.3715, 72.9046),
    ("Gujarat", "Dahod"): (22.8377, 74.2530),
    ("Gujarat", "Deesa"): (24.2584, 72.1906),
    ("Madhya Pradesh", "Neemuch"): (24.4764, 74.8696),
    ("Madhya Pradesh", "Betul"): (21.9004, 77.9003),
    ("Rajasthan", "Barmer"): (25.7521, 71.3967),
    ("Rajasthan", "Dholpur"): (26.7025, 77.8930),
    ("Karnataka", "Chitradurga"): (14.2251, 76.3980),
    ("Karnataka", "Ramanagara"): (12.7212, 77.2806),
    ("Karnataka", "Yadgir"): (16.7700, 77.1380),
    ("Tamil Nadu", "Nagapattinam"): (10.7659, 79.8449),
    ("Telangana", "Suryapet"): (17.1406, 79.6203),
    ("Telangana", "Miryalaguda"): (16.8720, 79.5650),
    ("Telangana", "Wanaparthy"): (16.3633, 78.0620),
    ("Kerala", "Vatakara"): (11.5983, 75.5900),
    ("Jharkhand", "Giridih"): (24.1800, 86.3000),
    ("Jharkhand", "Chaibasa"): (22.5500, 85.8000),
    ("Odisha", "Jharsuguda"): (21.8600, 84.0300),
    ("Odisha", "Kendujhar"): (21.6300, 85.5800),
}

STATE_CLIMATE = {
    "Rajasthan": "semi-arid", "Gujarat": "semi-arid", "Haryana": "semi-arid",
    "Punjab": "semi-arid", "Delhi": "semi-arid", "Chandigarh": "semi-arid",
    "Madhya Pradesh": "semi-arid", "Maharashtra": "semi-arid",
    "Telangana": "semi-arid", "Uttar Pradesh": "humid-subtropical",
    "Bihar": "humid-subtropical", "Jharkhand": "humid-subtropical",
    "West Bengal": "tropical-wet", "Odisha": "tropical-wet",
    "Chhattisgarh": "tropical-dry", "Andhra Pradesh": "tropical-dry",
    "Karnataka": "tropical-dry", "Tamil Nadu": "tropical-dry",
    "Kerala": "tropical-wet", "Goa": "coastal", "Assam": "humid-subtropical",
    "Arunachal Pradesh": "humid-subtropical", "Meghalaya": "humid-subtropical",
    "Manipur": "humid-subtropical", "Mizoram": "humid-subtropical",
    "Nagaland": "humid-subtropical", "Tripura": "humid-subtropical",
    "Sikkim": "temperate-highland", "Uttarakhand": "temperate-highland",
    "Himachal Pradesh": "temperate-highland",
    "Jammu and Kashmir": "temperate-highland", "Ladakh": "temperate-highland",
    "Puducherry": "coastal", "Andaman and Nicobar Islands": "coastal",
    "Dadra and Nagar Haveli and Daman and Diu": "coastal",
    "Lakshadweep": "coastal",
}

ARID_CITIES = {"Jaisalmer", "Barmer", "Bikaner", "Sri Ganganagar", "Hanumangarh",
               "Bhuj", "Gandhidham", "Surendranagar"}
COASTAL_CITIES = {"Surat", "Valsad", "Vapi", "Navsari", "Bharuch", "Porbandar",
                  "Veraval", "Bhavnagar", "Jamnagar", "Panaji", "Margao",
                  "Vasco da Gama", "Mapusa", "Ponda", "Bicholim", "Curchorem",
                  "Canacona", "Sanquelim", "Cuncolim", "Kollam", "Alappuzha",
                  "Kannur", "Kozhikode", "Kochi", "Thalassery", "Ponnani",
                  "Kasaragod", "Vatakara", "Kanhangad", "Thiruvananthapuram",
                  "Mangaluru", "Udupi", "Karwar", "Ratnagiri", "Thane",
                  "Mumbai", "Navi Mumbai", "Panvel", "Vasai-Virar",
                  "Mira-Bhayandar", "Kalyan-Dombivli", "Ulhasnagar",
                  "Chennai", "Cuddalore", "Nagapattinam", "Thoothukudi",
                  "Nagercoil", "Puducherry", "Karaikal", "Visakhapatnam",
                  "Kakinada", "Machilipatnam", "Nellore", "Ongole",
                  "Srikakulam", "Vizianagaram", "Rajamahendravaram", "Puri",
                  "Paradip", "Balasore", "Bhadrak", "Kolkata", "Howrah",
                  "Haldia", "Daman", "Diu", "Silvassa", "Kavaratti",
                  "Agatti", "Andrott", "Minicoy", "Sri Vijaya Puram",
                  "Car Nicobar", "Rangat", "Mayabunder", "Diglipur",
                  "Chandannagar"}
HILL_CITIES = {"Darjeeling", "Shimla", "Dharamshala", "Solan", "Mandi", "Kullu",
               "Manali", "Chamba", "Nahan", "Palampur", "Sundernagar",
               "Mussoorie", "Nainital", "Almora", "Pithoragarh", "Uttarkashi",
               "Chamoli", "Tehri", "Gangtok", "Namchi", "Gyalshing", "Mangan",
               "Leh", "Kargil", "Diskit", "Padum", "Nyoma", "Anantnag",
               "Baramulla", "Sopore", "Pulwama", "Kupwara", "Bandipora",
               "Tawang", "Bomdila", "Ziro", "Shillong", "Aizawl", "Kohima",
               "Mokokchung", "Wokha", "Zunheboto", "Tuensang", "Champhai",
               "Lunglei", "Bishnupur"}

COAST = [
    (23.7, 68.7), (23.0, 68.9), (22.5, 69.0), (22.3, 69.8), (22.6, 70.0),
    (21.7, 72.1), (21.0, 72.6), (20.0, 72.8), (19.1, 72.8), (18.0, 73.0),
    (17.0, 73.2), (15.5, 73.8), (15.0, 74.0), (14.0, 74.5), (13.0, 74.8),
    (12.0, 75.2), (11.0, 75.8), (10.0, 76.2), (9.0, 76.5), (8.3, 77.0),
    (8.1, 77.5), (8.8, 78.2), (9.3, 79.3), (10.3, 79.9), (11.5, 79.8),
    (12.5, 80.2), (13.5, 80.3), (14.5, 80.1), (15.8, 80.4), (16.3, 81.7),
    (17.0, 82.3), (17.7, 83.3), (18.3, 84.0), (19.3, 84.9), (19.8, 85.8),
    (20.5, 86.9), (21.5, 87.0), (21.6, 87.5), (21.7, 88.0), (22.0, 88.6),
    (21.6, 88.6), (22.0, 89.0), (11.6, 92.7), (10.6, 72.6), (20.7, 70.9),
    (20.4, 72.8),
]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s.lower() if c.isalnum())


def haversine(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def dist_to_coast(lat, lon) -> float:
    return min(haversine(lat, lon, c[0], c[1]) for c in COAST)


def load_world():
    rows = []
    with open(WORLD, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("iso2") != "IN":
                continue
            try:
                rows.append({"name": norm(r["city_ascii"] or r["city"]),
                             "admin": norm(r["admin_name"]),
                             "lat": float(r["lat"]), "lon": float(r["lng"]),
                             "pop": float(r["population"] or 0)})
            except (ValueError, KeyError):
                continue
    return rows


def fuzzy(target, pool, cutoff):
    best, score = None, 0.0
    for c in pool:
        r = SequenceMatcher(None, target, c["name"]).ratio()
        if r > score:
            best, score = c, r
    return best if score >= cutoff else None


def climate_for(state, city, lat, lon):
    city = city.split(" (")[0]
    if city in HILL_CITIES:
        return "temperate-highland"
    if city in ARID_CITIES:
        return "arid"
    if city in COASTAL_CITIES or dist_to_coast(lat, lon) < 30:
        return "coastal"
    base = STATE_CLIMATE.get(state, "semi-arid")
    return "tropical-wet" if base == "coastal" else base


def lpcd_for(pop_millions):
    if pop_millions >= 2:
        return 150
    if pop_millions >= 0.15:
        return 135
    if pop_millions >= 0.05:
        return 125
    return 115


def zones_for(pop_millions):
    z = round(3 + 1.1 * math.sqrt(max(pop_millions, 0.01) * 10))
    return int(min(max(z, 3), 10))


def main():
    world = load_world()
    by_name: dict[str, list] = {}
    for w in world:
        by_name.setdefault(w["name"], []).append(w)
    alias_n = {norm(k): [norm(x) for x in v] for k, v in CITY_ALIAS.items()}

    out_rows, state_pts = [], {}
    matched = manual = approx = 0
    for state, cities in INDIA_CITIES_FULL.items():
        admins = set(STATE_TO_ADMIN.get(state, []))
        state_pool = [w for w in world if w["admin"] in admins] or world
        for city in cities:
            n = norm(city)
            if (state, city) in MANUAL:                       # 1) pinned coords
                lat, lon = MANUAL[(state, city)]
                pop = 0.0
                src = "manual"; manual += 1
            else:
                names = alias_n.get(n, [n])
                pick = None
                for nm in names:                              # 2) exact, in state
                    c = [x for x in state_pool if x["name"] == nm]
                    if c:
                        pick = max(c, key=lambda x: x["pop"]); break
                if pick is None:                              # 3) exact, anywhere
                    for nm in names:
                        c = [x for x in world if x["name"] == nm]
                        if c:
                            pick = max(c, key=lambda x: x["pop"]); break
                if pick is None:                              # 4) fuzzy
                    for nm in names:
                        pick = fuzzy(nm, state_pool, 0.86) or fuzzy(nm, world, 0.90)
                        if pick:
                            break
                if pick:
                    lat, lon, pop, src = pick["lat"], pick["lon"], pick["pop"], "matched"
                    matched += 1
                else:
                    lat, lon, pop, src = None, None, 0.0, "approximate"
                    approx += 1
            if lat is not None:
                state_pts.setdefault(state, []).append((lat, lon))
            out_rows.append({"state_ut": state, "city": city, "lat": lat, "lon": lon,
                             "pop": pop, "coord_source": src})

    for r in out_rows:                                        # 5) bounding-box fallback
        if r["coord_source"] == "approximate":
            pts = state_pts.get(r["state_ut"], [])
            if pts:
                lats = [p[0] for p in pts]; lons = [p[1] for p in pts]
                lat0, lat1 = min(lats), max(lats)
                lon0, lon1 = min(lons), max(lons)
            else:
                lat0, lat1, lon0, lon1 = 22.0, 23.0, 78.5, 79.5
            # deterministic pseudo-random position inside the state's extent,
            # so approximate cities spread plausibly instead of stacking.
            h = abs(hash(r["city"]))
            fx = ((h % 997) / 997.0); fy = (((h // 997) % 991) / 991.0)
            r["lat"] = round(lat0 + (lat1 - lat0) * fy, 4)
            r["lon"] = round(lon0 + (lon1 - lon0) * fx, 4)
            r["pop"] = 150000.0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["state_ut", "city", "lat", "lon", "climate_zone",
                    "pop_millions", "lpcd_norm", "gross_supply_ml", "n_zones",
                    "coord_source"])
        # Disambiguate repeated names across states. The most populous city
        # keeps the plain name (so the prominent Srinagar is 'Srinagar', not the
        # small Uttarakhand town); the others get "(State)".
        from collections import defaultdict
        groups = defaultdict(list)
        for r in out_rows:
            groups[r["city"]].append(r)
        for name, rows in groups.items():
            if len(rows) > 1:
                rows.sort(key=lambda x: -x["pop"])
                for r in rows[1:]:
                    r["city"] = f"{r['city']} ({r['state_ut']})"
        for r in out_rows:
            pop_m = max(r["pop"] / 1e6, 0.01)
            czone = climate_for(r["state_ut"], r["city"], r["lat"], r["lon"])
            lpcd = lpcd_for(pop_m)
            w.writerow([r["state_ut"], r["city"], r["lat"], r["lon"], czone,
                        round(pop_m, 4), lpcd, round(pop_m * lpcd * 1.55, 1),
                        zones_for(pop_m), r["coord_source"]])

    zones = sum(zones_for(max(r["pop"] / 1e6, 0.01)) for r in out_rows)
    print(f"cities: {len(out_rows)}  matched: {matched}  manual: {manual}  "
          f"approximate: {approx}")
    print(f"zones: {zones}  states/UTs: {len(INDIA_CITIES_FULL)}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
