"""Period labelling helpers — never say 'last period' without a date."""
from __future__ import annotations

from datetime import date, datetime
from typing import TypeVar

_HasPeriod = TypeVar("_HasPeriod")


def is_future_month(period: date, as_of: date | None = None) -> bool:
    """True when ``period`` falls in a month that has not started yet.

    The current month counts as valid: a weekly dam reading or a month-to-date
    count legitimately carries the current month's period.
    """
    as_of = as_of or date.today()
    return (period.year, period.month) > (as_of.year, as_of.month)


def drop_future_points(
    points: list[_HasPeriod],
    as_of: date | None = None,
) -> list[_HasPeriod]:
    """Remove points dated beyond the current month.

    Some City datasets carry budget or forecast rows for the rest of the
    financial year in the same column as actuals. Ingesting those unfiltered
    made the Pulse report "energy down 9.5%, November to December 2026" in
    August 2026 — a movement between two months that had not happened. Nothing
    downstream can tell an actual from a projection once it is a MetricPoint,
    so they are dropped at the boundary.
    """
    return [p for p in points if not is_future_month(p.period, as_of)]


def format_month(value: date | datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value[:10])
        except ValueError:
            return value
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%B %Y")


def format_month_short(value: date | datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value[:10])
        except ValueError:
            return value
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%b %Y")
