"""Economic factor monitoring."""
import pytest

import economics


def test_operating_cost_per_kl():
    # treatment 14.5 + 0.28 * 7.2 = 16.516
    assert abs(economics.operating_cost_per_kl(7.2, 14.5, 0.28) - 16.516) < 1e-6


def test_energy_cost():
    assert economics.energy_cost_inr(100, 8.0) == 800.0
    with pytest.raises(ValueError):
        economics.energy_cost_inr(-1, 8.0)


def test_state_has_provenance_for_every_variable():
    s = economics.get_state()
    for v in s["variables"]:
        assert {"name", "value", "unit", "source", "kind"} <= set(v)


def test_estimate_operating_cost_daily():
    s = economics.get_state()
    est = economics.estimate_operating_cost(1000.0, s)
    assert est["period"] == "day"
    assert est["energy_kwh"] > 0
    assert est["total_operating_cost_inr"] > 0
    assert est["is_estimate"] is True


def test_manual_override_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(economics, "OVERRIDE_FILE", tmp_path / "ov.json")
    economics.save_override("electricity_tariff_inr_per_kwh", 9.9, "test", kind="manual")
    s = economics.get_state()
    assert s["by_name"]["electricity_tariff_inr_per_kwh"]["value"] == 9.9
    assert s["by_name"]["electricity_tariff_inr_per_kwh"]["kind"] == "manual"
