"""
India-wide city registry for the Smart Water Redistribution system.

Design goal: the SAME model must serve any selected city. Every city carries a
uniform set of meta-features (climate zone, population, per-capita norm, supply
capacity) so that a global demand model can transfer across locations, and so
the UI can switch between cities on a live map.

Coverage: all 28 states + 8 Union Territories, with 3-8 major cities each,
spanning every corner of the country (from Leh and Kargil in the north to
Kanyakumari-side Tirunelveli in the south, Bhuj in the west to Itanagar in
the east).
"""

# climate_zone: one of "arid", "semi-arid", "tropical-wet", "tropical-dry",
#               "humid-subtropical", "temperate-highland", "coastal"
# pop_millions: approximate urban agglomeration population (2021-24 scale)
# lpcd_norm: normative litres per capita per day the city aims to supply
# supply_ml: approximate city bulk water supply capacity, million litres/day
# zones: number of district-metered zones (DMAs) the model reasons over

INDIA_CITIES = {
    # ---------------- States ----------------
    "Andhra Pradesh": [
        ("Visakhapatnam", 17.6868, 83.2185, "coastal", 2.4, 135, 720, 10),
        ("Vijayawada", 16.5062, 80.6480, "tropical-dry", 1.5, 135, 430, 8),
        ("Guntur", 16.3067, 80.4365, "tropical-dry", 0.9, 135, 250, 6),
        ("Tirupati", 13.6288, 79.4192, "tropical-dry", 0.5, 135, 150, 5),
        ("Nellore", 14.4426, 79.9865, "coastal", 0.6, 135, 170, 5),
        ("Kurnool", 15.8281, 78.0373, "semi-arid", 0.5, 135, 140, 5),
    ],
    "Arunachal Pradesh": [
        ("Itanagar", 27.0844, 93.6053, "humid-subtropical", 0.4, 135, 60, 4),
        ("Tawang", 27.5861, 91.8594, "temperate-highland", 0.05, 100, 12, 3),
        ("Ziro", 27.5418, 93.8315, "humid-subtropical", 0.05, 120, 14, 3),
        ("Pasighat", 28.0667, 95.3333, "humid-subtropical", 0.06, 120, 18, 3),
    ],
    "Assam": [
        ("Guwahati", 26.1445, 91.7362, "humid-subtropical", 1.1, 135, 340, 8),
        ("Silchar", 24.8333, 92.7789, "humid-subtropical", 0.4, 135, 120, 5),
        ("Dibrugarh", 27.4728, 94.9120, "humid-subtropical", 0.3, 135, 95, 5),
        ("Jorhat", 26.7509, 94.2037, "humid-subtropical", 0.2, 135, 70, 4),
        ("Tezpur", 26.6338, 92.8000, "humid-subtropical", 0.1, 135, 40, 3),
    ],
    "Bihar": [
        ("Patna", 25.5941, 85.1376, "humid-subtropical", 2.5, 135, 640, 10),
        ("Gaya", 24.7955, 85.0002, "humid-subtropical", 0.6, 135, 160, 6),
        ("Bhagalpur", 25.2425, 86.9842, "humid-subtropical", 0.5, 135, 140, 5),
        ("Muzaffarpur", 26.1209, 85.3647, "humid-subtropical", 0.5, 135, 135, 5),
        ("Darbhanga", 26.1542, 85.8918, "humid-subtropical", 0.4, 135, 110, 5),
    ],
    "Chhattisgarh": [
        ("Raipur", 21.2514, 81.6296, "tropical-dry", 1.2, 135, 320, 8),
        ("Bhilai", 21.1938, 81.3509, "tropical-dry", 0.8, 135, 220, 6),
        ("Bilaspur", 22.0797, 82.1409, "tropical-dry", 0.5, 135, 140, 5),
        ("Korba", 22.3595, 82.7501, "tropical-dry", 0.3, 135, 90, 4),
    ],
    "Goa": [
        ("Panaji", 15.4909, 73.8278, "coastal", 0.3, 150, 120, 5),
        ("Margao", 15.2832, 73.9862, "coastal", 0.2, 150, 80, 4),
        ("Vasco da Gama", 15.3980, 73.8113, "coastal", 0.15, 150, 60, 3),
    ],
    "Gujarat": [
        ("Ahmedabad", 23.0225, 72.5714, "semi-arid", 7.0, 150, 1650, 14),
        ("Surat", 21.1702, 72.8311, "coastal", 6.5, 150, 1500, 14),
        ("Vadodara", 22.3072, 73.1812, "semi-arid", 1.8, 150, 460, 9),
        ("Rajkot", 22.3039, 70.8022, "semi-arid", 1.5, 150, 380, 8),
        ("Bhavnagar", 21.7645, 72.1519, "coastal", 0.6, 150, 160, 5),
        ("Jamnagar", 22.4707, 70.0577, "semi-arid", 0.6, 150, 155, 5),
        ("Gandhinagar", 23.2156, 72.6369, "semi-arid", 0.3, 150, 100, 4),
        ("Bhuj", 23.2420, 69.6669, "arid", 0.15, 150, 45, 3),
    ],
    "Haryana": [
        ("Gurugram", 28.4595, 77.0266, "semi-arid", 1.5, 150, 420, 8),
        ("Faridabad", 28.4089, 77.3178, "semi-arid", 1.4, 150, 380, 8),
        ("Panipat", 29.3909, 76.9635, "semi-arid", 0.5, 150, 140, 5),
        ("Ambala", 30.3782, 76.7767, "semi-arid", 0.4, 150, 110, 5),
        ("Hisar", 29.1492, 75.7217, "arid", 0.3, 150, 85, 4),
    ],
    "Himachal Pradesh": [
        ("Shimla", 31.1048, 77.1734, "temperate-highland", 0.2, 135, 55, 4),
        ("Dharamshala", 32.2190, 76.3234, "temperate-highland", 0.06, 120, 22, 3),
        ("Solan", 30.9045, 77.0967, "temperate-highland", 0.1, 120, 35, 3),
        ("Manali", 32.2432, 77.1892, "temperate-highland", 0.03, 110, 12, 3),
    ],
    "Jharkhand": [
        ("Ranchi", 23.3441, 85.3096, "humid-subtropical", 1.2, 135, 300, 8),
        ("Jamshedpur", 22.8046, 86.2029, "humid-subtropical", 1.3, 135, 330, 8),
        ("Dhanbad", 23.7957, 86.4304, "humid-subtropical", 1.2, 135, 290, 7),
        ("Bokaro", 23.6693, 86.1511, "humid-subtropical", 0.5, 135, 140, 5),
    ],
    "Karnataka": [
        ("Bengaluru", 12.9716, 77.5946, "temperate-highland", 12.5, 135, 2100, 16),
        ("Mysuru", 12.2958, 76.6394, "tropical-dry", 1.0, 135, 260, 7),
        ("Mangaluru", 12.9141, 74.8560, "coastal", 0.6, 135, 170, 5),
        ("Hubballi", 15.3647, 75.1240, "semi-arid", 0.9, 135, 220, 6),
        ("Belagavi", 15.8497, 74.4977, "semi-arid", 0.6, 135, 150, 5),
        ("Kalaburagi", 17.3297, 76.8343, "semi-arid", 0.5, 135, 120, 5),
    ],
    "Kerala": [
        ("Thiruvananthapuram", 8.5241, 76.9366, "tropical-wet", 1.0, 150, 300, 7),
        ("Kochi", 9.9312, 76.2673, "coastal", 2.1, 150, 620, 9),
        ("Kozhikode", 11.2588, 75.7804, "tropical-wet", 0.6, 150, 175, 5),
        ("Thrissur", 10.5276, 76.2144, "tropical-wet", 0.3, 150, 95, 4),
        ("Kannur", 11.8745, 75.3704, "tropical-wet", 0.2, 150, 65, 4),
    ],
    "Madhya Pradesh": [
        ("Bhopal", 23.2599, 77.4126, "semi-arid", 1.9, 135, 470, 9),
        ("Indore", 22.7196, 75.8577, "semi-arid", 2.0, 135, 510, 9),
        ("Gwalior", 26.2183, 78.1828, "semi-arid", 1.1, 135, 280, 7),
        ("Jabalpur", 23.1815, 79.9864, "tropical-dry", 1.2, 135, 300, 7),
        ("Ujjain", 23.1765, 75.7885, "semi-arid", 0.5, 135, 130, 5),
        ("Sagar", 23.8388, 78.7378, "semi-arid", 0.3, 135, 75, 4),
    ],
    "Maharashtra": [
        ("Mumbai", 19.0760, 72.8777, "coastal", 20.7, 135, 3750, 20),
        ("Pune", 18.5204, 73.8567, "semi-arid", 6.8, 150, 1550, 14),
        ("Nagpur", 21.1458, 79.0882, "tropical-dry", 2.9, 135, 720, 10),
        ("Nashik", 19.9975, 73.7898, "semi-arid", 1.6, 150, 400, 8),
        ("Thane", 19.2183, 72.9781, "coastal", 1.9, 135, 460, 8),
        ("Aurangabad", 19.8762, 75.3433, "semi-arid", 1.3, 135, 320, 7),
        ("Navi Mumbai", 19.0330, 73.0297, "coastal", 1.6, 135, 400, 8),
        ("Kolhapur", 16.7050, 74.2433, "tropical-dry", 0.6, 135, 150, 5),
    ],
    "Manipur": [
        ("Imphal", 24.8170, 93.9368, "humid-subtropical", 0.4, 135, 110, 5),
        ("Thoubal", 24.6333, 94.0167, "humid-subtropical", 0.05, 120, 15, 3),
        ("Churachandpur", 24.3333, 93.6833, "humid-subtropical", 0.05, 120, 14, 3),
    ],
    "Meghalaya": [
        ("Shillong", 25.5788, 91.8933, "temperate-highland", 0.4, 135, 110, 5),
        ("Tura", 25.5140, 90.2027, "humid-subtropical", 0.08, 120, 22, 3),
        ("Jowai", 25.4500, 92.2000, "humid-subtropical", 0.05, 120, 14, 3),
    ],
    "Mizoram": [
        ("Aizawl", 23.7271, 92.7176, "humid-subtropical", 0.3, 135, 85, 4),
        ("Lunglei", 22.8878, 92.7300, "humid-subtropical", 0.06, 120, 16, 3),
        ("Champhai", 23.4737, 93.3286, "humid-subtropical", 0.04, 120, 11, 3),
    ],
    "Nagaland": [
        ("Kohima", 25.6751, 94.1086, "humid-subtropical", 0.1, 135, 32, 3),
        ("Dimapur", 25.9063, 93.7276, "humid-subtropical", 0.15, 135, 45, 3),
        ("Mokokchung", 26.3200, 94.5200, "humid-subtropical", 0.04, 120, 12, 3),
    ],
    "Odisha": [
        ("Bhubaneswar", 20.2961, 85.8245, "tropical-wet", 1.2, 135, 330, 8),
        ("Cuttack", 20.4625, 85.8830, "tropical-wet", 0.7, 135, 190, 6),
        ("Rourkela", 22.2604, 84.8536, "tropical-wet", 0.6, 135, 165, 5),
        ("Puri", 19.8135, 85.8312, "coastal", 0.2, 135, 60, 4),
        ("Sambalpur", 21.4669, 83.9812, "tropical-wet", 0.3, 135, 80, 4),
    ],
    "Punjab": [
        ("Ludhiana", 30.9010, 75.8573, "semi-arid", 1.6, 150, 400, 8),
        ("Amritsar", 31.6340, 74.8723, "semi-arid", 1.2, 150, 300, 7),
        ("Jalandhar", 31.3260, 75.5762, "semi-arid", 0.9, 150, 220, 6),
        ("Patiala", 30.3398, 76.3869, "semi-arid", 0.5, 150, 120, 5),
        ("Bathinda", 30.2110, 74.9455, "arid", 0.3, 150, 75, 4),
    ],
    "Rajasthan": [
        ("Jaipur", 26.9124, 75.7873, "semi-arid", 3.9, 135, 900, 11),
        ("Jodhpur", 26.2389, 73.0243, "arid", 1.5, 135, 340, 8),
        ("Udaipur", 24.5854, 73.7125, "semi-arid", 0.6, 135, 150, 5),
        ("Kota", 25.2138, 75.8648, "semi-arid", 1.2, 135, 290, 7),
        ("Bikaner", 28.0229, 73.3119, "arid", 0.7, 135, 160, 5),
        ("Jaisalmer", 26.9157, 70.9083, "arid", 0.08, 135, 20, 3),
    ],
    "Sikkim": [
        ("Gangtok", 27.3389, 88.6065, "temperate-highland", 0.1, 120, 30, 3),
        ("Namchi", 27.1667, 88.3500, "temperate-highland", 0.02, 110, 7, 3),
        ("Gyalshing", 27.2833, 88.2667, "temperate-highland", 0.02, 110, 7, 3),
    ],
    "Tamil Nadu": [
        ("Chennai", 13.0827, 80.2707, "coastal", 11.5, 135, 2100, 16),
        ("Coimbatore", 11.0168, 76.9558, "semi-arid", 2.2, 135, 520, 9),
        ("Madurai", 9.9252, 78.1198, "tropical-dry", 1.6, 135, 380, 8),
        ("Tiruchirappalli", 10.7905, 78.7047, "tropical-dry", 1.0, 135, 240, 6),
        ("Salem", 11.6643, 78.1460, "semi-arid", 0.9, 135, 210, 6),
        ("Tirunelveli", 8.7139, 77.7567, "tropical-dry", 0.5, 135, 120, 5),
    ],
    "Telangana": [
        ("Hyderabad", 17.3850, 78.4867, "semi-arid", 9.5, 135, 2100, 14),
        ("Warangal", 17.9689, 79.5941, "semi-arid", 0.8, 135, 190, 6),
        ("Nizamabad", 18.6725, 78.0941, "semi-arid", 0.4, 135, 95, 5),
        ("Karimnagar", 18.4386, 79.1288, "semi-arid", 0.3, 135, 75, 4),
        ("Khammam", 17.2473, 80.1514, "tropical-dry", 0.3, 135, 70, 4),
    ],
    "Tripura": [
        ("Agartala", 23.8315, 91.2868, "humid-subtropical", 0.5, 135, 130, 5),
        ("Udaipur (Tripura)", 23.5333, 91.4833, "humid-subtropical", 0.04, 120, 11, 3),
        ("Dharmanagar", 24.3667, 92.1667, "humid-subtropical", 0.04, 120, 11, 3),
    ],
    "Uttar Pradesh": [
        ("Lucknow", 26.8467, 80.9462, "humid-subtropical", 3.8, 135, 880, 11),
        ("Kanpur", 26.4499, 80.3319, "humid-subtropical", 3.1, 135, 720, 10),
        ("Varanasi", 25.3176, 82.9739, "humid-subtropical", 1.6, 135, 380, 8),
        ("Agra", 27.1767, 78.0081, "semi-arid", 1.8, 135, 420, 8),
        ("Noida", 28.5355, 77.3910, "semi-arid", 0.7, 150, 180, 6),
        ("Ghaziabad", 28.6692, 77.4538, "semi-arid", 1.7, 150, 400, 8),
        ("Prayagraj", 25.4358, 81.8463, "humid-subtropical", 1.2, 135, 280, 7),
        ("Meerut", 28.9845, 77.7064, "semi-arid", 1.4, 150, 330, 7),
    ],
    "Uttarakhand": [
        ("Dehradun", 30.3165, 78.0322, "humid-subtropical", 0.8, 135, 190, 6),
        ("Haridwar", 29.9457, 78.1642, "humid-subtropical", 0.3, 135, 80, 4),
        ("Nainital", 29.3803, 79.4636, "temperate-highland", 0.05, 120, 15, 3),
        ("Rishikesh", 30.0869, 78.2676, "humid-subtropical", 0.1, 120, 28, 3),
    ],
    "West Bengal": [
        ("Kolkata", 22.5726, 88.3639, "tropical-wet", 15.1, 135, 2600, 16),
        ("Howrah", 22.5958, 88.2636, "tropical-wet", 1.1, 135, 280, 7),
        ("Siliguri", 26.7271, 88.3953, "humid-subtropical", 0.8, 135, 190, 6),
        ("Durgapur", 23.5204, 87.3119, "tropical-wet", 0.6, 135, 150, 5),
        ("Asansol", 23.6739, 86.9524, "tropical-wet", 0.6, 135, 150, 5),
        ("Darjeeling", 27.0360, 88.2627, "temperate-highland", 0.05, 120, 14, 3),
    ],
    # ---------------- Union Territories ----------------
    "Andaman and Nicobar Islands": [
        ("Port Blair", 11.6234, 92.7265, "coastal", 0.15, 150, 55, 3),
        ("Car Nicobar", 9.1667, 92.7667, "coastal", 0.02, 150, 8, 3),
    ],
    "Chandigarh": [
        ("Chandigarh", 30.7333, 76.7794, "semi-arid", 1.1, 150, 280, 7),
    ],
    "Dadra and Nagar Haveli and Daman and Diu": [
        ("Silvassa", 20.2738, 73.0152, "coastal", 0.1, 150, 35, 3),
        ("Daman", 20.3974, 72.8328, "coastal", 0.05, 150, 18, 3),
        ("Diu", 20.7144, 70.9874, "coastal", 0.03, 150, 10, 3),
    ],
    "Delhi": [
        ("New Delhi", 28.6139, 77.2090, "semi-arid", 3.0, 150, 720, 10),
        ("Dwarka", 28.5921, 77.0460, "semi-arid", 1.2, 150, 280, 7),
        ("Rohini", 28.7495, 77.0565, "semi-arid", 1.3, 150, 300, 7),
    ],
    "Jammu and Kashmir": [
        ("Srinagar", 34.0837, 74.7973, "temperate-highland", 1.2, 135, 220, 7),
        ("Jammu", 32.7266, 74.8570, "humid-subtropical", 0.7, 135, 160, 6),
        ("Anantnag", 33.7311, 75.1487, "temperate-highland", 0.15, 120, 35, 3),
        ("Baramulla", 34.1980, 74.3636, "temperate-highland", 0.1, 120, 25, 3),
    ],
    "Ladakh": [
        ("Leh", 34.1526, 77.5771, "arid", 0.04, 110, 12, 3),
        ("Kargil", 34.5539, 76.1349, "arid", 0.02, 110, 7, 3),
    ],
    "Lakshadweep": [
        ("Kavaratti", 10.5669, 72.6420, "coastal", 0.01, 150, 5, 3),
        ("Minicoy", 8.2833, 73.0500, "coastal", 0.01, 150, 4, 3),
    ],
    "Puducherry": [
        ("Puducherry", 11.9416, 79.8083, "coastal", 0.7, 150, 175, 5),
        ("Karaikal", 10.9254, 79.8380, "coastal", 0.1, 150, 30, 3),
        ("Mahe", 11.7000, 75.5333, "coastal", 0.05, 150, 14, 3),
        ("Yanam", 16.7333, 82.2167, "coastal", 0.04, 150, 12, 3),
    ],
}


import hashlib
import math
from pathlib import Path

from config import (CLIMATE_SUPPLY_FACTOR, DISASTER_PROFILE, POP_GROWTH_BASE,
                    POP_GROWTH_HILL_PENALTY, POP_GROWTH_MAX, POP_GROWTH_MIN,
                    POP_GROWTH_SIZE_COEFF, POP_GROWTH_SMALL_TOWN,
                    SUPPLY_UTILISATION)


def _jitter(name: str, spread: float = 1.0) -> float:
    """Deterministic pseudo-random value in [-spread, spread] from a city name.

    Used so that cities differ slightly from one another in a way that is
    reproducible run-to-run (no hidden randomness), while keeping the model
    explainable.
    """
    h = int(hashlib.md5(name.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return (h * 2.0 - 1.0) * spread


def growth_rate(city: dict) -> float:
    """Illustrative ANNUAL urban population growth rate (fraction, e.g. 0.021).

    Bigger cities grow a little slower in percentage terms. Only SMALL remote /
    hill towns are assumed to be stagnant or declining — a large highland metro
    like Bengaluru is treated as growing, not declining. Transparent model, not
    a census projection.
    """
    pop_k = max(city["pop_millions"] * 1000.0, 1.0)
    base = POP_GROWTH_BASE - POP_GROWTH_SIZE_COEFF * math.log10(pop_k)
    if (city["climate_zone"] == "temperate-highland"
            and city["pop_millions"] < POP_GROWTH_SMALL_TOWN):
        base -= POP_GROWTH_HILL_PENALTY
    base += 0.004 * _jitter(city["city"])
    return round(min(max(base, POP_GROWTH_MIN), POP_GROWTH_MAX), 4)


def reservoir_baseline(city: dict) -> float:
    """Illustrative reservoir/tank storage level (% of capacity) by climate."""
    base = {"arid": 42, "semi-arid": 55, "tropical-dry": 52, "tropical-wet": 74,
            "coastal": 70, "humid-subtropical": 76, "temperate-highland": 80}
    val = base.get(city["climate_zone"], 60) + 6.0 * _jitter(city["city"])
    return round(min(max(val, 20.0), 95.0), 1)


def disaster_profile(city: dict) -> dict:
    """Relative likelihood weights for each natural hazard, by climate zone."""
    return dict(DISASTER_PROFILE.get(city["climate_zone"], DISASTER_PROFILE["semi-arid"]))


_CSV = Path(__file__).resolve().parent / "data" / "cities_full.csv"
_CSV_CACHE: list | None = None


def _from_csv() -> list:
    """Load the expanded registry built by build_cities.py (584 cities)."""
    import csv
    out = []
    with open(_CSV, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            czone = r["climate_zone"]
            base = {
                "city": r["city"], "state_ut": r["state_ut"],
                "lat": float(r["lat"]), "lon": float(r["lon"]),
                "climate_zone": czone, "pop_millions": float(r["pop_millions"]),
                "lpcd_norm": float(r["lpcd_norm"]),
                "gross_supply_ml": float(r["gross_supply_ml"]),
                "n_zones": int(r["n_zones"]),
                "coord_source": r.get("coord_source", "matched"),
            }
            base["supply_ml"] = round(base["gross_supply_ml"] * SUPPLY_UTILISATION *
                                      CLIMATE_SUPPLY_FACTOR.get(czone, 1.0), 1)
            base["growth_rate"] = growth_rate(base)
            base["reservoir_baseline_pct"] = reservoir_baseline(base)
            base["disaster_profile"] = disaster_profile(base)
            out.append(base)
    return out


def all_cities():
    """The full registry: the expanded CSV if present, else the built-in list.

    Returns one dict per city with: state/UT, coordinates, climate zone,
    population, per-capita norm, gross and effective supply, zone count,
    annual growth rate, reservoir baseline and disaster profile.
    """
    global _CSV_CACHE
    if _CSV.exists():
        if _CSV_CACHE is None:
            _CSV_CACHE = _from_csv()
        return list(_CSV_CACHE)
    return _builtin_cities()


def _builtin_cities():
    out = []
    seen = set()
    for state, cities in INDIA_CITIES.items():
        for (name, lat, lon, czone, pop, lpcd, supply, zones) in cities:
            display = name
            if display in seen:
                display = f"{name} ({state})"
            seen.add(display)
            base = {
                "city": display, "state_ut": state, "lat": lat, "lon": lon,
                "climate_zone": czone, "pop_millions": pop, "lpcd_norm": lpcd,
                "supply_ml": round(supply * SUPPLY_UTILISATION *
                                   CLIMATE_SUPPLY_FACTOR.get(czone, 1.0), 1),
                "gross_supply_ml": supply, "n_zones": zones,
                "coord_source": "builtin",
            }
            base["growth_rate"] = growth_rate(base)
            base["reservoir_baseline_pct"] = reservoir_baseline(base)
            base["disaster_profile"] = disaster_profile(base)
            out.append(base)
    return out


def get_city(name):
    for c in all_cities():
        if c["city"].lower() == name.lower():
            return c
    return None


def cities_by_state():
    return {s: [c[0] for c in cs] for s, cs in INDIA_CITIES.items()}


if __name__ == "__main__":
    cities = all_cities()
    print(f"States/UTs: {len(INDIA_CITIES)}")
    print(f"Total cities: {len(cities)}")
    print(f"Total zones:  {sum(c['n_zones'] for c in cities)}")
