from datetime import date

from striops.core.models import MetricPoint, MetricSeries, Trend
from striops.forecasting import forecast_series


def _series(metric: str, values: list[float]) -> MetricSeries:
    return MetricSeries(
        entity_id="e1",
        metric=metric,
        points=[MetricPoint(period=date(2025, 1 + i, 1), value=v) for i, v in enumerate(values)],
    )


def test_rising_bad_metric_is_worsening():
    f = forecast_series(_series("refuse_service_requests", [100, 120, 140, 160, 180]))
    assert f.direction == Trend.WORSENING
    assert f.slope > 0
    assert f.projected_next > 180
    assert 0 < f.confidence <= 1


def test_falling_bad_metric_is_improving():
    f = forecast_series(_series("public_lighting_outages", [600, 560, 520, 500, 480]))
    assert f.direction == Trend.IMPROVING


def test_flat_metric_is_stable():
    f = forecast_series(_series("refuse_service_requests", [100, 101, 100, 99, 100]))
    assert f.direction == Trend.STABLE


def test_single_point_low_confidence():
    f = forecast_series(_series("refuse_service_requests", [100]))
    assert f.confidence <= 0.3
