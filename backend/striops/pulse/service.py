"""City Pulse — what moved between two named reporting periods.

The value of an operating system over a report is that nobody has to ask
"what changed?" — Striops answers it on every load, per metric, with direction
judged against the metric's polarity (is higher good or bad?), and with
explicit period labels so "last period" is never vague.
"""
from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from striops.core.anomaly import describe_break, is_suspect
from striops.core.config import Settings, get_settings
from striops.core.glossary import explain
from striops.core.periods import drop_future_points, format_month, format_month_short
from striops.persistence import Repository, get_repository

# True => a rising value is bad news (losses, backlogs, faults).
_HIGHER_IS_WORSE: dict[str, bool] = {
    "refuse_service_requests": True,
    "non_revenue_water_pct": True,
    "road_maintenance_backlog_km": True,
    "public_lighting_outages": True,
    "library_visits": False,
    "dam_storage": False,
    "dws_system_storage": False,
    "clinic_waiting_days": True,
    "ems_response_minutes": True,
    "system_energy_kwh": False,  # demand signal, not inherently good/bad
    "electricity_billed_kwh": False,  # demand/revenue signal
    "municipal_arrears_zar": True,  # rising debtors = fiscal distress
    "murder_count": True,
    "contact_crime_count": True,
    "population": False,
}

_LABELS: dict[str, str] = {
    "refuse_service_requests": "Refuse service requests",
    "non_revenue_water_pct": "Non-revenue water",
    "road_maintenance_backlog_km": "Road maintenance backlog",
    "public_lighting_outages": "Public lighting outages",
    "library_visits": "Library visits",
    "dam_storage": "Dam storage (City)",
    "dws_system_storage": "Dam storage (DWS system)",
    "clinic_waiting_days": "Clinic waiting days",
    "ems_response_minutes": "EMS response time",
    "system_energy_kwh": "System energy sent out",
    "electricity_billed_kwh": "Electricity billed",
    "municipal_arrears_zar": "Municipal arrears",
    "murder_count": "Murders (SAPS)",
    "contact_crime_count": "Contact crime (SAPS)",
    "population": "Population (Census)",
}

# Metrics wired to live / national public feeds (not demonstration seed).
_LIVE_METRICS: set[str] = {
    "dam_storage",
    "dws_system_storage",
    "system_energy_kwh",
    "electricity_billed_kwh",
    "municipal_arrears_zar",
    "public_lighting_outages",
    "refuse_service_requests",
    "murder_count",
    "contact_crime_count",
    "population",
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
    direction: str  # improving | worsening | flat | unverified
    sentence: str
    plain_language: str | None = None
    href: str
    latest_period: str | None = None
    previous_period: str | None = None
    provenance: str = "demonstration"  # live | demonstration
    # Set when the latest or previous reading breaks out of its own trailing
    # range. The month-over-month change is then reported as unverified rather
    # than asserted, because the likely cause is the extract, not the service.
    needs_verification: bool = False
    verification_note: str | None = None


class CityPulse(BaseModel):
    generated_at: str
    cadence: str = "monthly"
    data_through: str | None = None  # e.g. "February 2026"
    previous_period: str | None = None  # e.g. "January 2026"
    period_note: str
    items: list[PulseItem] = Field(default_factory=list)
    worsening_count: int = 0
    improving_count: int = 0
    unverified_count: int = 0


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
    # Freshness is the newest period across ALL series (not the last one iterated).
    all_periods: set = set()

    for series in repo.metric_series():
        # Guard again at read time: points already stored from an earlier ingest
        # would otherwise keep reporting movements between months that have not
        # happened yet.
        points = drop_future_points(sorted(series.points, key=lambda p: p.period))
        all_periods.update(p.period for p in points)
        if len(points) < 2:
            continue
        prev_pt, last_pt = points[-2], points[-1]
        prev, last = prev_pt.value, last_pt.value
        change = last - prev
        change_pct = (change / prev * 100) if prev else 0.0

        label = _LABELS.get(series.metric, series.metric.replace("_", " ").title())
        latest_label = format_month(last_pt.period)
        previous_label = format_month(prev_pt.period)

        # Screen both endpoints of the comparison — a broken previous month
        # invents a change just as readily as a broken latest one.
        values = [p.value for p in points]
        broken = next(
            (i for i in (len(values) - 1, len(values) - 2) if is_suspect(values, i)),
            None,
        )
        # Name the month when the break is in the baseline rather than the
        # latest reading, so the note cannot contradict the figure beside it.
        broken_label = (
            format_month(points[broken].period)
            if broken is not None and broken != len(values) - 1
            else None
        )
        verification_note = (
            describe_break(values, broken, period_label=broken_label)
            if broken is not None
            else None
        )
        needs_verification = verification_note is not None

        if needs_verification:
            direction = "unverified"
        elif abs(change_pct) < 0.5:
            direction = "flat"
        else:
            got_worse = (change > 0) == _HIGHER_IS_WORSE.get(series.metric, True)
            direction = "worsening" if got_worse else "improving"

        if needs_verification:
            # Full stop, not a dash: the note is a standalone sentence and may
            # name a different month than the reading quoted here.
            sentence = (
                f"{label}: {_fmt(last, series.unit)} in {format_month_short(last_pt.period)}. "
                f"{verification_note}"
            )
        else:
            verb = {
                "worsening": "up" if change > 0 else "down",
                "improving": "up" if change > 0 else "down",
                "flat": "flat",
            }[direction]
            sentence = (
                f"{label} {verb} {abs(change_pct):.1f}% "
                f"({format_month_short(prev_pt.period)} → {format_month_short(last_pt.period)}: "
                f"{_fmt(prev, series.unit)} → {_fmt(last, series.unit)})."
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
                latest_period=latest_label,
                previous_period=previous_label,
                provenance="live" if series.metric in _LIVE_METRICS else "demonstration",
                needs_verification=needs_verification,
                verification_note=verification_note,
            )
        )

    # Critical sectors first; libraries / secondary citizen signals last.
    _SECTOR_RANK = {
        "clinic_waiting_days": 0,
        "ems_response_minutes": 1,
        "murder_count": 2,
        "contact_crime_count": 3,
        "dam_storage": 4,
        "dws_system_storage": 5,
        "non_revenue_water_pct": 6,
        "road_maintenance_backlog_km": 7,
        "refuse_service_requests": 8,
        "public_lighting_outages": 9,
        "population": 80,
        "library_visits": 90,
    }
    order = {"worsening": 0, "improving": 1, "flat": 2, "unverified": 3}
    items.sort(
        key=lambda i: (
            0 if i.provenance == "live" else 1,  # live feeds first for the executive brief
            # Anything awaiting verification sits below the metrics that can
            # defend themselves — it must never lead the brief.
            1 if i.needs_verification else 0,
            _SECTOR_RANK.get(i.metric, 50),
            order[i.direction],
            -abs(i.change_pct),
        )
    )

    ordered_periods = sorted(all_periods)
    latest_date = ordered_periods[-1] if ordered_periods else None
    previous_date = ordered_periods[-2] if len(ordered_periods) >= 2 else None
    data_through = format_month(latest_date)
    previous_period = format_month(previous_date)
    if data_through and previous_period:
        period_note = (
            f"{data_through} vs {previous_period} (monthly operational series). "
            f"Data through {data_through}."
        )
    else:
        period_note = "No periods on record."

    return CityPulse(
        generated_at=datetime.now(UTC).isoformat(),
        cadence="monthly",
        data_through=data_through,
        previous_period=previous_period,
        period_note=period_note,
        items=items,
        worsening_count=sum(1 for i in items if i.direction == "worsening"),
        improving_count=sum(1 for i in items if i.direction == "improving"),
        unverified_count=sum(1 for i in items if i.needs_verification),
    )
