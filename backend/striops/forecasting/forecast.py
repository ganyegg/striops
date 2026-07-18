"""Trend forecasting for metric series."""
from __future__ import annotations

import numpy as np

from striops.core.models import Forecast, MetricSeries, Trend

# Metrics where an increase is bad (higher = worse). Everything else: higher = better.
_HIGHER_IS_WORSE = {
    "refuse_service_requests",
    "non_revenue_water_pct",
    "road_maintenance_backlog_km",
    "public_lighting_outages",
    "complaints",
    "clinic_waiting_days",
    "ems_response_minutes",
}


def _r_squared(y: np.ndarray, y_hat: np.ndarray) -> float:
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    if ss_tot == 0:
        return 1.0
    return max(0.0, 1.0 - ss_res / ss_tot)


def forecast_series(series: MetricSeries) -> Forecast:
    """Fit a linear trend and project one period ahead.

    `confidence` blends goodness-of-fit (R^2) with sample size, so a clean trend
    over many points is trusted more than a noisy two-point line.
    """
    values = series.values()
    n = len(values)
    if n < 2:
        return Forecast(
            entity_id=series.entity_id,
            metric=series.metric,
            direction=Trend.STABLE,
            slope=0.0,
            projected_next=values[0] if values else 0.0,
            confidence=0.2,
            contributing_factors=["insufficient history"],
        )

    x = np.arange(n, dtype=float)
    y = np.array(values, dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    y_hat = slope * x + intercept
    r2 = _r_squared(y, y_hat)
    projected = float(slope * n + intercept)

    mean = float(np.mean(y)) or 1.0
    pct_per_period = (slope / abs(mean)) * 100

    higher_is_worse = series.metric in _HIGHER_IS_WORSE
    if abs(pct_per_period) < 0.75:
        direction = Trend.STABLE
    elif (slope > 0) == higher_is_worse:
        direction = Trend.WORSENING
    else:
        direction = Trend.IMPROVING

    sample_factor = min(1.0, n / 8.0)
    confidence = round(0.35 + 0.5 * r2 * sample_factor + 0.15 * sample_factor, 3)
    confidence = min(0.98, confidence)

    factors = [
        f"{pct_per_period:+.1f}% per period over {n} periods",
        f"fit quality R^2={r2:.2f}",
    ]
    return Forecast(
        entity_id=series.entity_id,
        metric=series.metric,
        direction=direction,
        slope=round(float(slope), 4),
        projected_next=round(projected, 2),
        confidence=confidence,
        contributing_factors=factors,
    )
