"""City registry + factor models (population, disaster, abundance)."""

from city_registry import all_cities, disaster_profile
from models import abundance, disaster, population


def test_registry_has_all_derived_factors():
    c = all_cities()[0]
    for k in ("growth_rate", "reservoir_baseline_pct", "disaster_profile",
              "supply_ml", "climate_zone", "pop_millions"):
        assert k in c


def test_registry_coverage():
    cities = all_cities()
    assert len(cities) >= 100
    assert sum(c["n_zones"] for c in cities) > 500


def test_city_names_are_unique():
    names = [c["city"] for c in all_cities()]
    assert len(names) == len(set(names))


def test_zones_have_distinct_coordinates(raw):
    g = raw[raw["city"] == "Mumbai"]
    coords = g[["zone_id", "lat", "lon"]].drop_duplicates("zone_id")
    assert coords["lat"].nunique() > 1 and coords["lon"].nunique() > 1


def test_growth_rate_in_bounds_and_metropolis_grows():
    for c in all_cities():
        assert -0.02 <= c["growth_rate"] <= 0.05
    # a large highland metro must NOT be marked as declining
    blr = next(c for c in all_cities() if c["city"] == "Bengaluru")
    assert blr["growth_rate"] > 0


def test_disaster_profile_sums_reasonably():
    for c in all_cities()[:20]:
        assert abs(sum(disaster_profile(c).values()) - 1.0) < 0.2


def test_hazard_scores_normalised():
    c = all_cities()[0]
    s = disaster.hazard_scores(c, 7)
    assert abs(sum(s.values()) - 1.0) < 1e-3


def test_disaster_effects_blended_not_permanent():
    c = next(x for x in all_cities() if x["climate_zone"] == "coastal")
    d = disaster.analyse(c, 9)
    # an occasional hazard must not permanently crush supply
    assert 0.9 < d["expected_supply_multiplier"] <= 1.0
    assert 0.0 <= d["disaster_risk"] <= 1.0


def test_population_projection_and_trend():
    c = next(x for x in all_cities() if x["city"] == "Mumbai")
    p = population.analyse(c)
    assert p["trend"] in ("growing", "slow-growing", "stable", "declining")
    assert p["ten_year_pop_millions"] > 0
    assert p["projection"][0]["demand_factor"] == 1.0


def test_population_declining_small_hill_town():
    assert population.classify_trend(-0.01) == "declining"
    assert population.classify_trend(0.02) == "growing"


def test_abundance_bands_and_index_monotonic():
    assert abundance.classify(0.5) in ("abundance", "severe-abundance")
    assert abundance.classify(-0.5) == "severe-scarcity"
    assert abundance.abundance_index(0.0) == 50.0
    assert abundance.abundance_index(1.0) > abundance.abundance_index(-1.0)


def test_abundance_reports_drivers_for_every_factor():
    c = all_cities()[0]
    pop = population.analyse(c)
    dis = disaster.analyse(c)
    ab = abundance.analyse(c, demand_kl=100000.0, supply_ml=100.0,
                           rain_mm=5.0, temp_c=31.0, reservoir_pct=60.0,
                           disaster=dis, population=pop)
    names = " ".join(d["factor"] for d in ab["drivers"])
    assert "weather" in names and "population" in names and "disaster" in names
    assert ab["band"] in [b[2] for b in __import__("config").ABUNDANCE_BANDS]
