"""Risk assessment over the current facts."""
from __future__ import annotations

from helm.core.models import (
    BudgetLine,
    Entity,
    Evidence,
    Forecast,
    MetricSeries,
    Priority,
    Risk,
    Trend,
)
from helm.forecasting import forecast_series

# Per-metric knowledge: how much a worsening trend matters and what to do.
_METRIC_PROFILE: dict[str, dict] = {
    "refuse_service_requests": {
        "title": "Rising refuse service complaints",
        "impact": 0.65,
        "mitigation": "Expand collection routes and add contractor capacity before backlog compounds.",
        "unit_label": "requests/month",
    },
    "non_revenue_water_pct": {
        "title": "Escalating non-revenue water losses",
        "impact": 0.85,
        "mitigation": "Accelerate leak detection and pipe replacement in worst-performing zones.",
        "unit_label": "% losses",
    },
    "road_maintenance_backlog_km": {
        "title": "Growing road maintenance backlog",
        "impact": 0.7,
        "mitigation": "Reprioritise capital spend toward preventative resurfacing to slow backlog growth.",
        "unit_label": "km backlog",
    },
    "public_lighting_outages": {
        "title": "Public lighting reliability",
        "impact": 0.4,
        "mitigation": "Maintain current preventative maintenance cadence; monitor for regression.",
        "unit_label": "faults/month",
    },
    "library_visits": {
        "title": "Declining library engagement",
        "impact": 0.35,
        "mitigation": "Refresh programming and digital services to reverse footfall decline.",
        "unit_label": "visits/month",
    },
}


def _trend_multiplier(forecast: Forecast, values: list[float]) -> float:
    """Map a forecast to a 0.5-2.0 trend multiplier."""
    if forecast.direction == Trend.STABLE:
        return 1.0
    baseline = abs(sum(values) / len(values)) or 1.0
    intensity = min(1.0, abs(forecast.slope) / baseline * 6)
    if forecast.direction == Trend.WORSENING:
        return round(1.0 + intensity, 3)
    return round(1.0 - 0.5 * intensity, 3)


def _priority(score: float) -> Priority:
    if score >= 55:
        return Priority.CRITICAL
    if score >= 35:
        return Priority.HIGH
    if score >= 18:
        return Priority.MEDIUM
    return Priority.LOW


def assess_risks(
    service_areas: list[Entity],
    metric_series: list[MetricSeries],
    budget_lines: list[BudgetLine],
) -> list[Risk]:
    by_id = {e.id: e for e in service_areas}
    latest_budget: dict[str, BudgetLine] = {}
    for line in sorted(budget_lines, key=lambda b: b.financial_year):
        latest_budget[line.function_name] = line

    risks: list[Risk] = []
    for series in metric_series:
        profile = _METRIC_PROFILE.get(series.metric)
        if not profile:
            continue
        forecast = forecast_series(series)
        if forecast.direction == Trend.IMPROVING:
            continue  # improving metrics are handled by the opportunity engine

        values = series.values()
        owner_entity = by_id.get(series.entity_id)
        owner = owner_entity.properties.get("owner", "Unassigned") if owner_entity else "Unassigned"
        name = owner_entity.name if owner_entity else series.entity_id

        likelihood = round(min(0.95, 0.4 + 0.6 * forecast.confidence), 3)
        impact = profile["impact"]
        trend = _trend_multiplier(forecast, values)
        confidence = forecast.confidence

        evidence = [
            Evidence(
                label="Latest value",
                value=f"{values[-1]:,.1f} {profile['unit_label']}",
                source="metrics",
            ),
            Evidence(
                label="Projected next period",
                value=f"{forecast.projected_next:,.1f} {profile['unit_label']}",
                source="forecast",
            ),
            Evidence(label="Trend", value=", ".join(forecast.contributing_factors), source="forecast"),
        ]

        budget_fn = owner_entity.properties.get("budget_function") if owner_entity else None
        if budget_fn and budget_fn in latest_budget:
            bl = latest_budget[budget_fn]
            evidence.append(
                Evidence(
                    label="Budget utilisation",
                    value=f"{bl.utilisation * 100:.0f}% of R{bl.budget / 1e9:.2f}bn",
                    source="treasury",
                )
            )
            if bl.utilisation < 0.9 and profile["impact"] >= 0.6:
                impact = min(1.0, impact + 0.1)  # underspending while service degrades compounds risk

        risk = Risk(
            id=f"risk-{series.entity_id}-{series.metric}",
            title=profile["title"],
            reason=(
                f"{name}: {series.metric.replace('_', ' ')} is {forecast.direction.value} "
                f"({forecast.contributing_factors[0]}), projected to reach "
                f"{forecast.projected_next:,.0f} next period."
            ),
            likelihood=likelihood,
            impact=impact,
            trend=trend,
            confidence=confidence,
            priority=Priority.LOW,  # replaced below
            owner=owner,
            mitigation=profile["mitigation"],
            evidence=evidence,
            forecast=forecast,
        )
        risk.priority = _priority(risk.score)
        risks.append(risk)

    risks.sort(key=lambda r: r.score, reverse=True)
    return risks
