"""Period labelling helpers — never say 'last period' without a date."""
from __future__ import annotations

from datetime import date, datetime


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
