"""Tests for period validity — no reporting on months that have not happened."""
from datetime import date

from striops.core.models import MetricPoint
from striops.core.periods import drop_future_points, format_month, is_future_month


def test_current_month_is_not_the_future():
    """A weekly dam reading legitimately carries the current month."""
    assert not is_future_month(date(2026, 8, 1), as_of=date(2026, 8, 14))
    assert not is_future_month(date(2026, 8, 31), as_of=date(2026, 8, 1))


def test_next_month_onwards_is_the_future():
    assert is_future_month(date(2026, 9, 1), as_of=date(2026, 8, 14))
    assert is_future_month(date(2026, 12, 1), as_of=date(2026, 8, 14))
    assert is_future_month(date(2027, 1, 1), as_of=date(2026, 12, 31))


def test_past_periods_are_kept():
    assert not is_future_month(date(2011, 10, 1), as_of=date(2026, 8, 14))


def test_forecast_rows_are_dropped_from_a_series():
    """The energy dataset carried Sep-Dec 2026 alongside August actuals."""
    points = [
        MetricPoint(period=date(2026, 6, 1), value=795.0),
        MetricPoint(period=date(2026, 7, 1), value=780.0),
        MetricPoint(period=date(2026, 8, 1), value=760.0),
        MetricPoint(period=date(2026, 11, 1), value=725.0),
        MetricPoint(period=date(2026, 12, 1), value=656.0),
    ]
    kept = drop_future_points(points, as_of=date(2026, 8, 14))
    assert [p.period.month for p in kept] == [6, 7, 8]


def test_dropping_is_a_no_op_for_a_clean_series():
    points = [MetricPoint(period=date(2026, m, 1), value=1.0) for m in (4, 5, 6)]
    assert drop_future_points(points, as_of=date(2026, 8, 14)) == points


def _label_is_future(label: str | None, today: date) -> bool:
    """Reverse a "%B %Y" label back to a month so it can be range-checked."""
    if not label:
        return False
    for year in (today.year - 1, today.year, today.year + 1, today.year + 2):
        for month in range(1, 13):
            if format_month(date(year, month, 1)) == label:
                return is_future_month(date(year, month, 1), today)
    return False


def test_metric_series_screens_forecast_rows_held_in_the_store(monkeypatch):
    """The store itself holds forecast rows, so this injects them.

    Postgres still has Sep-Dec 2026 energy rows ingested before the source
    filter existed. The seed extract is clean, so a test that only reads the
    seed would pass with the screen removed.
    """
    from striops.persistence import repository as repo_module

    today = date.today()
    this_month = today.replace(day=1)
    next_year = date(today.year + 1, today.month, 1)
    monkeypatch.setattr(repo_module, "_national_metric_series", lambda *_: [])
    monkeypatch.setattr(
        repo_module,
        "_load_seed",
        lambda name: [
            {
                "entity_id": "CPT",
                "metric": "system_energy_kwh",
                "unit": "kWh",
                "points": [
                    {"period": this_month.isoformat(), "value": 808.0},
                    {"period": next_year.isoformat(), "value": 656.0},
                ],
            },
            {
                "entity_id": "CPT",
                "metric": "pure_forecast",
                "unit": "kWh",
                "points": [{"period": next_year.isoformat(), "value": 1.0}],
            },
        ],
    )

    repo = repo_module.Repository()
    repo._use_pg = False  # deterministic regardless of a local Postgres
    by_metric = {s.metric: s for s in repo.metric_series()}

    assert [p.period for p in by_metric["system_energy_kwh"].points] == [this_month]
    assert "pure_forecast" not in by_metric, "a series left empty should be dropped"


def test_metric_series_never_hands_out_future_points():
    """The screen sits at the read boundary, so every consumer inherits it."""
    from striops.persistence import get_repository

    today = date.today()
    for series in get_repository().metric_series():
        assert series.points, "an emptied series should be dropped, not returned"
        for point in series.points:
            assert not is_future_month(point.period, today), (
                f"{series.metric} carries future point {point.period}"
            )


def test_snapshot_freshness_is_never_in_the_future():
    """Regression: the header advertised "Through December 2026" in August 2026.

    Pulse was screened but the snapshot computed freshness straight off the
    store, so the two disagreed by four months on the same page.
    """
    from striops.snapshot.service import build_city_snapshot

    snapshot = build_city_snapshot()
    today = date.today()
    assert not _label_is_future(snapshot.data_through, today), (
        f"snapshot reports future freshness {snapshot.data_through}"
    )
    assert not _label_is_future(snapshot.previous_period, today)


def test_pulse_never_reports_a_future_period():
    """End-to-end: whatever the store holds, the brief stays in the past."""
    from striops.pulse import build_city_pulse

    pulse = build_city_pulse()
    today = date.today()
    for item in pulse.items:
        for label in (item.latest_period, item.previous_period):
            assert label, "every pulse item must carry period labels"
        latest = item.latest_period
        # Labels are "%B %Y"; rebuild the month to compare.
        for month in range(1, 13):
            for year in (today.year, today.year + 1):
                if format_month(date(year, month, 1)) == latest:
                    assert not is_future_month(date(year, month, 1), today), (
                        f"{item.metric} reports future period {latest}"
                    )
