"""Tests for the SAPS crime connector.

Network is never touched — the quarterly workbooks are ~11MB each. What is
tested here is the URL contract, the station join, the merge that lets a newer
SAPS release win, and that the shipped extract is actually current.
"""
from datetime import date

import pytest

from striops.ingestion.national.saps_crime import (
    _merge_monthly,
    fetch_crime_series,
    station_keys,
    station_population,
)
from striops.ingestion.national.saps_quarterly import normalise_station, quarter_url


def test_quarter_url_follows_the_saps_financial_year():
    """Q4 of FY2025/26 is Jan-Mar 2026 and lives under the FY start year."""
    url = quarter_url(2025, 4)
    assert url == (
        "https://www.saps.gov.za/services/downloads/2025/2025-2026_-_4th_Quarter_WEB.xlsx"
    )
    assert "1st" in quarter_url(2025, 1)
    assert "2nd" in quarter_url(2025, 2)
    assert "3rd" in quarter_url(2025, 3)


def test_quarter_url_rejects_a_bad_quarter():
    with pytest.raises(ValueError):
        quarter_url(2025, 5)


def test_station_names_fold_across_punctuation():
    """SAPS and the station register disagree on apostrophes."""
    assert normalise_station("Gordon's Bay") == normalise_station("Gordons Bay")
    assert normalise_station("Simon's Town") == "simons town"
    assert normalise_station("  MITCHELLS   PLAIN ") == "mitchells plain"
    assert normalise_station(None) == ""


def test_cape_town_station_register_is_shipped():
    keys = station_keys("CPT")
    assert len(keys) == 62, "Cape Town has 62 SAPS station precincts"
    assert "mitchells plain" in keys
    assert "simons town" in keys
    assert station_population("CPT") > 4_000_000


def test_unknown_municipality_yields_no_stations():
    assert station_keys("NOPE") == set()
    assert station_population("NOPE") is None


def test_merge_lets_the_newer_saps_release_win():
    """SAPS revises counts between releases, so a re-read replaces a month."""
    existing = [
        {"year": 2025, "month": 8, "count": 355},
        {"year": 2025, "month": 9, "count": 324},
    ]
    merged = _merge_monthly(existing, {date(2025, 9, 1): 320.0, date(2025, 10, 1): 329.0})
    assert merged == [
        {"year": 2025, "month": 8, "count": 355},
        {"year": 2025, "month": 9, "count": 320},
        {"year": 2025, "month": 10, "count": 329},
    ]


def test_merge_keeps_periods_in_order():
    merged = _merge_monthly([], {date(2026, 3, 1): 274.0, date(2026, 1, 1): 276.0})
    assert [(r["year"], r["month"]) for r in merged] == [(2026, 1), (2026, 3)]


def test_shipped_extract_reaches_the_latest_published_quarter():
    """The seed must not silently rot back to 2025 — that was the original bug."""
    series = {s.metric: s for s in fetch_crime_series("CPT")}
    assert "murder_count" in series
    assert "contact_crime_count" in series
    latest = max(p.period for p in series["murder_count"].points)
    assert latest >= date(2026, 3, 1), f"crime extract is stale at {latest}"
    # SAPS publishes a quarter at a time, so months arrive in threes with no gaps.
    periods = sorted(p.period for p in series["murder_count"].points)
    assert len(periods) == len(set(periods)), "duplicate months in the extract"
