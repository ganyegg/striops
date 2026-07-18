"""Curated comparative packs — side-by-side trends and decision-useful ratios."""
from __future__ import annotations

from pydantic import BaseModel, Field

from striops.core.glossary import explain
from striops.core.models import MetricSeries
from striops.core.periods import format_month
from striops.persistence import Repository, get_repository


class SeriesPoint(BaseModel):
    period: str
    value: float


class ComparativeSeries(BaseModel):
    entity_id: str
    metric: str
    label: str
    unit: str | None = None
    higher_is_worse: bool
    points: list[SeriesPoint] = Field(default_factory=list)
    latest: float | None = None
    previous: float | None = None
    change_pct: float | None = None
    href: str
    plain_language: str | None = None


class StrategicRatio(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    interpretation: str
    why_it_matters: str


class ComparativePack(BaseModel):
    id: str
    title: str
    eyebrow: str
    why_it_matters: str
    decision_anchor: str
    series: list[ComparativeSeries] = Field(default_factory=list)
    ratio: StrategicRatio | None = None


class ComparativesReport(BaseModel):
    municipality: str
    data_through: str | None = None
    packs: list[ComparativePack] = Field(default_factory=list)
    note: str = (
        "Packs only include ratios that share periods and support a real decision. "
        "Every series links to its full metric report."
    )


_LABELS = {
    "non_revenue_water_pct": "Non-revenue water",
    "dam_storage": "Dam storage",
    "clinic_waiting_days": "Clinic waiting days",
    "ems_response_minutes": "EMS response time",
}

_HIGHER_IS_WORSE = {
    "non_revenue_water_pct": True,
    "dam_storage": False,
    "clinic_waiting_days": True,
    "ems_response_minutes": True,
}


def _find(series_list: list[MetricSeries], entity_id: str, metric: str) -> MetricSeries | None:
    for s in series_list:
        if s.entity_id == entity_id and s.metric == metric:
            return s
    return None


def _to_comp(series: MetricSeries) -> ComparativeSeries:
    points = sorted(series.points, key=lambda p: p.period)
    latest = previous = change_pct = None
    if points:
        latest = points[-1].value
    if len(points) >= 2:
        previous = points[-2].value
        if previous:
            change_pct = round((latest - previous) / previous * 100, 1)  # type: ignore[operator]
    gloss = explain(series.metric)
    return ComparativeSeries(
        entity_id=series.entity_id,
        metric=series.metric,
        label=_LABELS.get(series.metric, series.metric.replace("_", " ").title()),
        unit=series.unit,
        higher_is_worse=_HIGHER_IS_WORSE.get(series.metric, True),
        points=[
            SeriesPoint(
                period=p.period.isoformat() if hasattr(p.period, "isoformat") else str(p.period)[:10],
                value=p.value,
            )
            for p in points
        ],
        latest=latest,
        previous=previous,
        change_pct=change_pct,
        href=f"/metrics/{series.entity_id}/{series.metric}",
        plain_language=gloss["in_one_line"] if gloss else None,
    )


def _water_ratio(nrw: ComparativeSeries, dams: ComparativeSeries) -> StrategicRatio | None:
    if nrw.latest is None or dams.latest is None:
        return None
    # Headroom = unused dam capacity; losses rising while headroom falls is stress.
    headroom = 100.0 - dams.latest
    gap = round(nrw.latest - headroom, 1)
    if gap > 0:
        interp = (
            f"NRW ({nrw.latest}%) exceeds unused dam headroom ({headroom:.1f}%). "
            "You are losing more water than the buffer you still have in the dams."
        )
    else:
        interp = (
            f"Dam headroom ({headroom:.1f}%) still exceeds NRW ({nrw.latest}%). "
            "Losses are serious, but bulk storage still provides a cushion."
        )
    return StrategicRatio(
        key="loss_storage_gap",
        label="Loss–storage gap",
        value=gap,
        unit="pp (NRW − dam headroom)",
        interpretation=interp,
        why_it_matters=(
            "If losses outpace remaining storage buffer, pipe fixes and conservation "
            "compete with capital for water security — leadership must sequence both."
        ),
    )


def _health_ratio(wait: ComparativeSeries, ems: ComparativeSeries) -> StrategicRatio | None:
    if wait.latest is None or ems.latest is None or ems.latest <= 0:
        return None
    # Waiting days expressed relative to a 15-minute EMS benchmark pressure.
    pressure = round(wait.latest * (ems.latest / 15.0), 2)
    return StrategicRatio(
        key="access_pressure_index",
        label="Access pressure index",
        value=pressure,
        unit="clinic-days × (EMS min / 15)",
        interpretation=(
            f"Clinic waits ({wait.latest} days) scaled by EMS response "
            f"({ems.latest} min vs 15-min benchmark) → {pressure}."
        ),
        why_it_matters=(
            "Primary care queues and emergency response share the same patient pathway. "
            "When both worsen, the City is losing access at the front door and the back door."
        ),
    )


def build_comparatives(repo: Repository | None = None, municipality: str = "CPT") -> ComparativesReport:
    repo = repo or get_repository()
    series_list = repo.metric_series()
    packs: list[ComparativePack] = []
    data_through = None

    nrw_s = _find(series_list, "svc-water", "non_revenue_water_pct")
    dams_s = _find(series_list, "svc-water", "dam_storage")
    if nrw_s and dams_s:
        nrw, dams = _to_comp(nrw_s), _to_comp(dams_s)
        if nrw.points:
            data_through = format_month(nrw.points[-1].period)
        packs.append(
            ComparativePack(
                id="water_stress",
                title="Water stress",
                eyebrow="Dams vs losses",
                why_it_matters=(
                    "Dam storage is the City's bulk water bank balance; non-revenue water is "
                    "what leaks or goes unbilled after production. Read them together."
                ),
                decision_anchor="Sequence pipe replacement vs demand management before summer peak.",
                series=[dams, nrw],
                ratio=_water_ratio(nrw, dams),
            )
        )

    wait_s = _find(series_list, "svc-health", "clinic_waiting_days")
    ems_s = _find(series_list, "svc-health", "ems_response_minutes")
    if wait_s and ems_s:
        wait, ems = _to_comp(wait_s), _to_comp(ems_s)
        packs.append(
            ComparativePack(
                id="health_access",
                title="Health access",
                eyebrow="Clinics vs EMS",
                why_it_matters=(
                    "Clinic waiting days and EMS response times are the two clearest "
                    "operational access signals for City Health."
                ),
                decision_anchor="Protect PHC capacity and EMS units where both series worsen.",
                series=[wait, ems],
                ratio=_health_ratio(wait, ems),
            )
        )

    # Only complementary pairs that share a pathway are contrasted: water (dams vs
    # losses) and health (clinics vs EMS). Unrelated series get their own metric report.
    rank = {"water_stress": 0, "health_access": 1}
    packs.sort(key=lambda p: rank.get(p.id, 5))

    return ComparativesReport(municipality=municipality, data_through=data_through, packs=packs)

