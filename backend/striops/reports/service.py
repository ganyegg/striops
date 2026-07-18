"""Assemble drill-down reports for risks and metrics.

Every report includes the full time series (for charts), forecast projection,
period-over-period stats, narrative, and reference links to authentic sources.
"""
from __future__ import annotations

from datetime import date

from striops.core.glossary import explain_risk_id
from striops.core.models import (
    ChartPoint,
    Forecast,
    IndicatorReport,
    MetricReport,
    MetricSeries,
    MetricStats,
    ReferenceLink,
    RiskReport,
    ScoreBreakdown,
)
from striops.domains import get_domain, get_municipality
from striops.forecasting import forecast_series
from striops.opportunity_engine import find_opportunities
from striops.persistence import Repository, get_repository
from striops.risk_engine import assess_risks
from striops.valuation import attach_valuations

# Domain indicator key → optional live metric series for charting.
_INDICATOR_METRIC: dict[str, tuple[str, str]] = {
    "nrw": ("svc-water", "non_revenue_water_pct"),
    "dams": ("svc-water", "dam_storage"),
    "clinic_wait": ("svc-health", "clinic_waiting_days"),
    "ems_response": ("svc-health", "ems_response_minutes"),
    "refuse_requests": ("svc-solid-waste", "refuse_service_requests"),
    "backlog": ("svc-roads", "road_maintenance_backlog_km"),
    "c3": ("svc-solid-waste", "refuse_service_requests"),
}

# Metric → human label, related domain, and public references.
_METRIC_META: dict[str, dict] = {
    "refuse_service_requests": {
        "label": "Refuse service requests",
        "domain": "waste",
        "budget_function": "Solid Waste Management",
        "references": [
            {
                "label": "City Open Data — service notifications / waste",
                "publisher": "City of Cape Town Open Data Portal",
                "url": "https://odp.capetown.gov.za",
                "as_of": "rolling",
                "note": "C3 / service request volumes by directorate.",
            },
            {
                "label": "Solid Waste Management budget line",
                "publisher": "City of Cape Town",
                "url": "https://www.capetown.gov.za/Family%20and%20home/meet-the-city/city-budget",
                "as_of": "2026/27 budget",
            },
        ],
    },
    "non_revenue_water_pct": {
        "label": "Non-revenue water",
        "domain": "water",
        "budget_function": "Water and Sanitation",
        "references": [
            {
                "label": "Western Cape dam levels (weekly)",
                "publisher": "Dept. of Water & Sanitation",
                "url": "https://www.dws.gov.za/Hydrology/Weekly/ProvinceWeek.aspx?region=WC",
                "as_of": "weekly",
            },
            {
                "label": "Water & sanitation capital programme",
                "publisher": "City of Cape Town",
                "url": "https://www.capetown.gov.za/Family%20and%20home/meet-the-city/city-budget",
                "as_of": "2026/27 budget",
                "note": "R16.7bn water & sanitation capital in the City of Hope budget.",
            },
            {
                "label": "Municipal Money — Cape Town (CPT)",
                "publisher": "National Treasury",
                "url": "https://municipaldata.treasury.gov.za/profiles/municipality-CPT-city-of-cape-town/",
                "as_of": "live",
            },
        ],
    },
    "road_maintenance_backlog_km": {
        "label": "Road maintenance backlog",
        "domain": "transport",
        "budget_function": "Roads and Transport",
        "references": [
            {
                "label": "Roads & stormwater capital",
                "publisher": "City of Cape Town",
                "url": "https://www.capetown.gov.za/Family%20and%20home/meet-the-city/city-budget",
                "as_of": "2026/27 budget",
                "note": "R3.7bn roads & stormwater vs R16.7bn water capital.",
            },
            {
                "label": "Municipal Money — Cape Town (CPT)",
                "publisher": "National Treasury",
                "url": "https://municipaldata.treasury.gov.za/profiles/municipality-CPT-city-of-cape-town/",
                "as_of": "live",
            },
        ],
    },
    "public_lighting_outages": {
        "label": "Public lighting outages",
        "domain": "energy",
        "budget_function": "Electricity",
        "references": [
            {
                "label": "Electricity grid capital",
                "publisher": "City of Cape Town",
                "url": "https://www.capetown.gov.za/Family%20and%20home/meet-the-city/city-budget",
                "as_of": "2026/27 budget",
            },
            {
                "label": "Open Data Portal",
                "publisher": "City of Cape Town",
                "url": "https://odp.capetown.gov.za",
                "as_of": "live",
            },
        ],
    },
    "library_visits": {
        "label": "Library visits",
        "domain": "governance_policies",
        "budget_function": "Community and Libraries",
        "references": [
            {
                "label": "Community & libraries budget",
                "publisher": "City of Cape Town",
                "url": "https://www.capetown.gov.za/Family%20and%20home/meet-the-city/city-budget",
                "as_of": "2026/27 budget",
            },
            {
                "label": "IDP 2022–2027",
                "publisher": "City of Cape Town",
                "url": "https://www.capetown.gov.za/Family%20and%20home/meet-the-city/our-vision-for-the-city/cape-towns-integrated-development-plan",
                "as_of": "2022–2027",
            },
        ],
    },
    "dam_storage": {
        "label": "Dam storage",
        "domain": "water",
        "budget_function": "Water and Sanitation",
        "references": [
            {
                "label": "Dam Levels from 2000 (measured)",
                "publisher": "City of Cape Town Open Data Portal",
                "url": "https://odp-cctegis.opendata.arcgis.com/datasets/cctegis::dam-levels-from-2000",
                "as_of": "live",
                "note": "Big-6 storage % — pulled directly by Striops.",
            },
            {
                "label": "Western Cape dam levels (weekly)",
                "publisher": "Dept. of Water & Sanitation",
                "url": "https://www.dws.gov.za/Hydrology/Weekly/ProvinceWeek.aspx?region=WC",
                "as_of": "weekly",
            },
        ],
    },
    "system_energy_kwh": {
        "label": "System energy sent out",
        "domain": "energy",
        "budget_function": "Electricity",
        "references": [
            {
                "label": "System Energy (monthly)",
                "publisher": "City of Cape Town Open Data Portal",
                "url": "https://odp-cctegis.opendata.arcgis.com/datasets/cctegis::system-energy-2017-to-2026",
                "as_of": "live",
                "note": "Total system energy sent out (kWh) — pulled directly by Striops.",
            },
        ],
    },
}


def _parse_risk_id(risk_id: str) -> tuple[str, str] | None:
    """risk-{entity_id}-{metric} → (entity_id, metric)."""
    if not risk_id.startswith("risk-"):
        return None
    rest = risk_id[len("risk-") :]
    for metric in _METRIC_META:
        suffix = f"-{metric}"
        if rest.endswith(suffix):
            return rest[: -len(suffix)], metric
    # Fallback: split on first known entity prefix patterns
    parts = rest.split("-", 2)
    if len(parts) >= 3 and parts[0] == "svc":
        # svc-water-non_revenue_water_pct
        entity = f"{parts[0]}-{parts[1]}"
        metric = rest[len(entity) + 1 :]
        return entity, metric
    return None


def _parse_opp_id(opp_id: str) -> tuple[str, str] | None:
    """opp-efficiency-{entity}-{metric} or opp-underspend-..."""
    if opp_id.startswith("opp-efficiency-"):
        rest = opp_id[len("opp-efficiency-") :]
        for metric in _METRIC_META:
            suffix = f"-{metric}"
            if rest.endswith(suffix):
                return rest[: -len(suffix)], metric
    return None


def _stats(series: MetricSeries) -> MetricStats:
    points = sorted(series.points, key=lambda p: p.period)
    if not points:
        return MetricStats(latest=0.0)
    values = [p.value for p in points]
    latest = values[-1]
    previous = values[-2] if len(values) > 1 else None
    change = (latest - previous) if previous is not None else None
    change_pct = (change / previous * 100.0) if previous not in (None, 0) and change is not None else None
    return MetricStats(
        latest=latest,
        previous=previous,
        change=round(change, 3) if change is not None else None,
        change_pct=round(change_pct, 2) if change_pct is not None else None,
        period_start=str(points[0].period),
        period_end=str(points[-1].period),
        n_points=len(points),
        min_value=min(values),
        max_value=max(values),
        mean=round(sum(values) / len(values), 3),
    )


def _chart_points(series: MetricSeries) -> list[ChartPoint]:
    return [
        ChartPoint(period=str(p.period), value=p.value, kind="actual")
        for p in sorted(series.points, key=lambda x: x.period)
    ]


def _add_months(d: date, months: int) -> date:
    year = d.year + (d.month + months - 1) // 12
    month = (d.month + months - 1) % 12 + 1
    return date(year, month, 1)


def _projected_points(series: MetricSeries, forecast: Forecast, n: int = 3) -> list[ChartPoint]:
    points = sorted(series.points, key=lambda p: p.period)
    if not points:
        return []
    last = points[-1].period
    out: list[ChartPoint] = [
        ChartPoint(period=str(last), value=points[-1].value, kind="projected"),
    ]
    for i in range(1, n + 1):
        period = _add_months(last, i) if isinstance(last, date) else last
        value = points[-1].value + forecast.slope * i
        out.append(ChartPoint(period=str(period), value=round(value, 2), kind="projected"))
    return out


def _refs(metric: str) -> list[ReferenceLink]:
    meta = _METRIC_META.get(metric, {})
    return [ReferenceLink(**r) for r in meta.get("references", [])]


def _find_series(repo: Repository, entity_id: str, metric: str) -> MetricSeries | None:
    for s in repo.metric_series():
        if s.entity_id == entity_id and s.metric == metric:
            return s
    return None


def build_metric_report(
    entity_id: str,
    metric: str,
    repo: Repository | None = None,
) -> MetricReport:
    repo = repo or get_repository()
    series = _find_series(repo, entity_id, metric)
    if series is None:
        raise KeyError(f"Unknown metric series: {entity_id}/{metric}")

    entity = next((e for e in repo.service_areas() if e.id == entity_id), None)
    entity_name = entity.name if entity else entity_id
    owner = entity.properties.get("owner") if entity else None
    department = entity.properties.get("department") if entity else None
    meta = _METRIC_META.get(metric, {})
    forecast = forecast_series(series)
    stats = _stats(series)

    change_txt = ""
    if stats.change_pct is not None:
        change_txt = f" Latest month-on-month change: {stats.change_pct:+.1f}%."
    narrative = (
        f"{meta.get('label', metric.replace('_', ' ').title())} for {entity_name} "
        f"covers {stats.n_points} periods from {stats.period_start} to {stats.period_end}. "
        f"Current value is {stats.latest:,.1f}{(' ' + series.unit) if series.unit else ''}; "
        f"trend is {forecast.direction.value} "
        f"({', '.join(forecast.contributing_factors)}). "
        f"Projected next period: {forecast.projected_next:,.1f}.{change_txt}"
    )

    related_risk_id = f"risk-{entity_id}-{metric}"
    risks = assess_risks(repo.service_areas(), repo.metric_series(), repo.budget_lines())
    if not any(r.id == related_risk_id for r in risks):
        related_risk_id = None

    return MetricReport(
        entity_id=entity_id,
        entity_name=entity_name,
        metric=metric,
        metric_label=meta.get("label", metric.replace("_", " ").title()),
        unit=series.unit,
        series=_chart_points(series),
        projected=_projected_points(series, forecast),
        forecast=forecast,
        stats=stats,
        owner=owner,
        department=department,
        related_domain_id=meta.get("domain"),
        related_risk_id=related_risk_id,
        narrative=narrative,
        references=_refs(metric),
    )


def build_risk_report(risk_id: str, repo: Repository | None = None) -> RiskReport:
    repo = repo or get_repository()
    risks = assess_risks(repo.service_areas(), repo.metric_series(), repo.budget_lines())
    risks, _ = attach_valuations(risks, [], repo.metric_series())
    from striops.demographics import attach_affected

    risks = attach_affected(risks)
    risk = next((r for r in risks if r.id == risk_id), None)

    # Also allow looking up via opportunity id that maps to a metric.
    parsed = _parse_risk_id(risk_id) if risk is None else _parse_risk_id(risk.id if risk else risk_id)
    if risk is None and parsed:
        # Synthesize from metric if assess_risks skipped improving series
        entity_id, metric = parsed
        series = _find_series(repo, entity_id, metric)
        if series is None:
            raise KeyError(f"Unknown risk: {risk_id}")
        # Fall through: build a lightweight risk from opportunity path — still raise
        raise KeyError(
            f"Risk '{risk_id}' is not currently active (metric may be improving). "
            f"Open the metric report instead: /metrics/{entity_id}/{metric}"
        )
    if risk is None:
        raise KeyError(f"Unknown risk: {risk_id}")

    parsed = _parse_risk_id(risk.id)
    metric_report: MetricReport | None = None
    budget_fn = None
    domain_id = None
    if parsed:
        entity_id, metric = parsed
        metric_report = build_metric_report(entity_id, metric, repo=repo)
        meta = _METRIC_META.get(metric, {})
        budget_fn = meta.get("budget_function")
        domain_id = meta.get("domain")

    breakdown = ScoreBreakdown(
        likelihood=risk.likelihood,
        impact=risk.impact,
        trend=risk.trend,
        confidence=risk.confidence,
        score=risk.score,
    )

    what_changed: list[str] = []
    if metric_report and metric_report.stats.change_pct is not None:
        what_changed.append(
            f"Latest period moved {metric_report.stats.change_pct:+.1f}% "
            f"({metric_report.stats.previous:,.1f} → {metric_report.stats.latest:,.1f})"
        )
    if risk.forecast:
        what_changed.append(
            f"Direction: {risk.forecast.direction.value}; "
            f"projected next = {risk.forecast.projected_next:,.1f}"
        )
        what_changed.extend(risk.forecast.contributing_factors)
    for ev in risk.evidence[:3]:
        what_changed.append(f"{ev.label}: {ev.value}")

    recommended = [
        risk.mitigation,
        "Fund the response from adjacent underspend where available (fiscally neutral).",
        "Set a monthly review against this series until the trend reverses.",
    ]

    refs = list(metric_report.references) if metric_report else []
    # Deduplicate by URL
    seen: set[str] = set()
    unique_refs: list[ReferenceLink] = []
    for r in refs:
        if r.url in seen:
            continue
        seen.add(r.url)
        unique_refs.append(r)

    narrative = (
        f"{risk.title} (score {risk.score}, {risk.priority.value}) is owned by {risk.owner}. "
        f"{risk.reason} "
        f"Score breakdown: likelihood {risk.likelihood:.2f} × impact {risk.impact:.2f} "
        f"× trend {risk.trend:.2f} × confidence {risk.confidence:.2f}."
    )

    gloss = explain_risk_id(risk.id)
    return RiskReport(
        risk=risk,
        score_breakdown=breakdown,
        metric_report=metric_report,
        related_domain_id=domain_id,
        related_budget_function=budget_fn,
        narrative=narrative,
        what_changed=what_changed,
        recommended_actions=recommended,
        references=unique_refs,
        plain_language=gloss["definition"] if gloss else None,
        term=gloss["term"] if gloss else None,
        in_one_line=gloss["in_one_line"] if gloss else None,
    )


def build_indicator_report(
    code: str,
    domain_id: str,
    indicator_key: str,
    repo: Repository | None = None,
) -> IndicatorReport:
    repo = repo or get_repository()
    muni = get_municipality(code)
    if muni is None:
        raise KeyError(f"Unknown municipality: {code}")
    try:
        profile = get_domain(code, domain_id)
    except KeyError as exc:
        raise KeyError(str(exc)) from exc

    indicator = next((i for i in profile.indicators if i.key == indicator_key), None)
    if indicator is None:
        raise KeyError(f"Unknown indicator: {domain_id}/{indicator_key}")

    source = next((s for s in profile.sources if s.id == indicator.source_id), None)
    related = [i for i in profile.indicators if i.key != indicator_key][:4]

    refs = [
        ReferenceLink(
            label=s.title,
            publisher=s.publisher,
            url=s.url,
            as_of=str(s.retrieved_at) if s.retrieved_at else None,
            note=s.coverage,
        )
        for s in profile.sources
    ]

    related_metric = None
    link = _INDICATOR_METRIC.get(indicator_key)
    if link:
        related_metric = {"entity_id": link[0], "metric": link[1]}

    # Related active risks whose domain matches
    risks = assess_risks(repo.service_areas(), repo.metric_series(), repo.budget_lines())
    related_risk_ids: list[str] = []
    for r in risks:
        parsed = _parse_risk_id(r.id)
        if parsed and _METRIC_META.get(parsed[1], {}).get("domain") == domain_id:
            related_risk_ids.append(r.id)

    narrative = (
        f"{indicator.label} for {profile.municipality} is currently "
        f"{indicator.value} (as of {indicator.as_of}). "
        f"Verification status: {indicator.verification.value}. "
        f"Confidence {indicator.confidence:.0%}."
    )
    if indicator.method:
        narrative += f" Method: {indicator.method}"

    return IndicatorReport(
        municipality_code=code.upper(),
        municipality_name=muni.name,
        domain_id=domain_id,
        domain_name=profile.name,
        indicator=indicator,
        source=source,
        domain_summary=profile.summary,
        watchpoints=profile.watchpoints,
        related_indicators=related,
        related_risk_ids=related_risk_ids,
        related_metric=related_metric,
        narrative=narrative,
        references=refs,
    )


def build_opportunity_redirect(opp_id: str, repo: Repository | None = None) -> str | None:
    """If an opportunity maps to a metric, return that metric path hint."""
    repo = repo or get_repository()
    parsed = _parse_opp_id(opp_id)
    if parsed:
        entity_id, metric = parsed
        return f"/metrics/{entity_id}/{metric}"
    # Underspend opportunities → budget domain
    if opp_id.startswith("opp-underspend-"):
        return "/CPT/domains/budget"
    # Try linked metric from active opportunities
    opps = find_opportunities(repo.service_areas(), repo.metric_series(), repo.budget_lines())
    opp = next((o for o in opps if o.id == opp_id), None)
    if opp and opp.id.startswith("opp-efficiency-"):
        return build_opportunity_redirect(opp.id, repo)
    return None
