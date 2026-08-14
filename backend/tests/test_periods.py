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
