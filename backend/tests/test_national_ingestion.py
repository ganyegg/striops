"""Smoke tests for national connectors (offline / seed-friendly)."""
from __future__ import annotations

from striops.feeds import build_feeds_report
from striops.ingestion.national.census_baselines import fetch_census_series, write_census_overlay
from striops.ingestion.national.saps_crime import fetch_crime_series, write_crime_overlay
from striops.ingestion.treasury import _FUNCTION_GROUPS, _seed_budget_lines


def test_census_series_from_seed():
    series = fetch_census_series("CPT")
    assert series is not None
    assert series.metric == "population"
    assert series.points[-1].value == 4772846
    assert write_census_overlay("CPT") is True


def test_saps_crime_series_from_seed_extract():
    series = fetch_crime_series("CPT")
    metrics = {s.metric for s in series}
    assert "murder_count" in metrics
    assert "contact_crime_count" in metrics
    murder = next(s for s in series if s.metric == "murder_count")
    assert len(murder.points) >= 12
    assert write_crime_overlay("CPT") is True


def test_treasury_function_groups_cover_service_areas():
    # Must stay aligned with datasets/seed/service_areas.json budget_function names
    # used by opportunities / graph FUNDED_BY (except safety/population).
    assert "Water and Sanitation" in _FUNCTION_GROUPS
    assert "Electricity" in _FUNCTION_GROUPS
    seed = _seed_budget_lines()
    assert seed, "seed budget lines required for CI fallback"


def test_feeds_include_national_ids():
    report = build_feeds_report()
    ids = {f.id for f in report.feeds}
    assert {"saps", "dws", "census", "agsa", "treasury"} <= ids


def test_pulse_includes_saps_crime_from_national_seed():
    from striops.pulse import build_city_pulse

    pulse = build_city_pulse()
    metrics = {i.metric for i in pulse.items}
    assert "murder_count" in metrics
    assert "contact_crime_count" in metrics
    murder = next(i for i in pulse.items if i.metric == "murder_count")
    assert murder.provenance == "live"
    assert murder.latest_period  # has a MoM period label
