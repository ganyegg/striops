"""Forecast engine: turns a metric time series into a trend + projection.

Uses a robust linear trend (numpy least-squares) by default, and Prophet if it
is installed. Output feeds the Risk Engine's `Trend` factor and the Executive
Brief's emerging-trends section — always with contributing factors, never a bare
number.
"""
from striops.forecasting.forecast import forecast_series

__all__ = ["forecast_series"]
