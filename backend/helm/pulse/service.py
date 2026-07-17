"""City Pulse — what moved since the last reporting period.

The value of an operating system over a report is that nobody has to ask
"what changed?" — Helm answers it on every load, per metric, with direction
judged against the metric's polarity (is higher good or bad?).
"""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from helm.core.config import Settings, get_settings
from helm.core.glossary import explain
from helm.persistence import Repository, get_repository

# True => a rising value is bad news (losses, backlogs, faults).
_HIGHER_IS_WORSE: dict[str, bool] = {
    "refuse_service_requests": True,
    "non_revenue_water_pct": True,
    "road_maintenance_backlog_km": True,
    "public_lighting_outages": True,
    "library_visits": False,
}

_LABELS: dict[str, str] = {
    "refuse_service_requests": "Refuse service requests",
    "non_revenue_water_pct": "Non-revenue water",
    "road_maintenance_backlog_km": "Road maintenance backlog",
    "public_lighting_outages": "Public lighting outages",
    "library_visits": "Library visits",
}


class PulseItem(BaseModel):
    entity_id: str
    metric: str
    label: str
    unit: str | None = None
    latest: float
    previous: float
    change: float
    change_pct: float
    direction: str  # improving | worsening | flat
    sentence: str
    plain_language: str | None = None
    href: str


class CityPulse(BaseModel):
    generated_at: str
    period_note: str
    items: list[PulseItem] = Field(default_factory=list)
    worsening_count: int = 0
    improving_count: int = 0


def _fmt(value: float, unit: str | None) -> str:
    text = f"{value:,.1f}".rstrip("0").rstrip(".")
    return f"{text} {unit}" if unit else text


def build_city_pulse(
    repo: Repository | None = None,
    settings: Settings | None = None,
) -> CityPulse:
    settings = settings or get_settings()
    repo = repo or get_repository(settings)

    items: list[PulseItem] = []
    latest_period: str | None = None

    for series in repo.metric_series():
        points = sorted(series.points, key=lambda p: p.period)
        if len(points) < 2:
            continue
        prev, last = points[-2].value, points[-1].value
        latest_period = str(points[-1].period)
        change = last - prev
        change_pct = (change / prev * 100) if prev else 0.0

        label = _LABELS.get(series.metric, series.metric.replace("_", " ").title())
        if abs(change_pct) < 0.5:
            direction = "flat"
        else:
            got_worse = (change > 0) == _HIGHER_IS_WORSE.get(series.metric, True)
            direction = "worsening" if got_worse else "improving"

        verb = {"worsening": "up" if change > 0 else "down",
                "improving": "up" if change > 0 else "down",
                "flat": "flat"}[direction]
        sentence = (
            f"{label} {verb} {abs(change_pct):.1f}% vs the previous period "
            f"({_fmt(prev, series.unit)} \u2192 {_fmt(last, series.unit)})."
        )
        glossary = explain(series.metric)

        items.append(
            PulseItem(
                entity_id=series.entity_id,
                metric=series.metric,
                label=label,
                unit=series.unit,
                latest=round(last, 2),
                previous=round(prev, 2),
                change=round(change, 2),
                change_pct=round(change_pct, 1),
                direction=direction,
                sentence=sentence,
                plain_language=glossary["in_one_line"] if glossary else None,
                href=f"/metrics/{series.entity_id}/{series.metric}",
            )
        )

    # Worst news first: worsening by magnitude, then improving, then flat.
    order = {"worsening": 0, "improving": 1, "flat": 2}
    items.sort(key=lambda i: (order[i.direction], -abs(i.change_pct)))

    return CityPulse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        period_note=f"Latest period on record: {latest_period}" if latest_period else "No periods on record.",
        items=items,
        worsening_count=sum(1 for i in items if i.direction == "worsening"),
        improving_count=sum(1 for i in items if i.direction == "improving"),
    )
