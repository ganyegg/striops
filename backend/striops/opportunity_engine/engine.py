"""Opportunity detection over budgets and operational metrics."""
from __future__ import annotations

from striops.core.models import (
    BudgetLine,
    Entity,
    Evidence,
    MetricSeries,
    Opportunity,
    Priority,
    Trend,
)
from striops.forecasting import forecast_series


def _priority_from_value(value_zar: float) -> Priority:
    if value_zar >= 500_000_000:
        return Priority.HIGH
    if value_zar >= 100_000_000:
        return Priority.MEDIUM
    return Priority.LOW


def find_opportunities(
    service_areas: list[Entity],
    metric_series: list[MetricSeries],
    budget_lines: list[BudgetLine],
) -> list[Opportunity]:
    opportunities: list[Opportunity] = []

    by_function: dict[str, Entity] = {
        e.properties.get("budget_function"): e for e in service_areas if e.properties.get("budget_function")
    }

    # 1) Budget underspend -> reallocation / delivery-acceleration opportunity.
    latest: dict[str, BudgetLine] = {}
    for line in sorted(budget_lines, key=lambda b: b.financial_year):
        latest[line.function_name] = line
    for fn, bl in latest.items():
        if bl.utilisation < 0.92 and bl.variance > 50_000_000:
            owner_entity = by_function.get(fn)
            owner = owner_entity.properties.get("owner", "Executive") if owner_entity else "Executive"
            opportunities.append(
                Opportunity(
                    id=f"opp-underspend-{fn.lower().replace(' ', '-')}",
                    title=f"Redeploy underspent {fn} budget",
                    reason=(
                        f"{fn} used only {bl.utilisation * 100:.0f}% of its "
                        f"R{bl.budget / 1e9:.2f}bn budget, leaving R{bl.variance / 1e9:.2f}bn unspent "
                        f"while related service demand rises "
                        f"(demonstration full-year financial_year={bl.financial_year}; "
                        f"not official FY2025/26 mid-year YTD to 31 Dec)."
                    ),
                    value_estimate=round(bl.variance, 0),
                    unit="ZAR",
                    confidence=0.7,
                    priority=_priority_from_value(bl.variance),
                    owner=owner,
                    action=(
                        f"Reallocate a portion of the R{bl.variance / 1e9:.2f}bn underspend to accelerate "
                        "delivery in the highest-demand wards this cycle."
                    ),
                    evidence=[
                        Evidence(label="Budget", value=f"R{bl.budget / 1e9:.2f}bn", source="treasury"),
                        Evidence(label="Actual", value=f"R{bl.actual / 1e9:.2f}bn", source="treasury"),
                        Evidence(label="Underspend", value=f"R{bl.variance / 1e9:.2f}bn", source="treasury"),
                    ],
                )
            )

    # 2) Improving operational metric -> efficiency dividend to redeploy.
    for series in metric_series:
        forecast = forecast_series(series)
        if forecast.direction != Trend.IMPROVING:
            continue
        owner_entity = next((e for e in service_areas if e.id == series.entity_id), None)
        owner = owner_entity.properties.get("owner", "Executive") if owner_entity else "Executive"
        name = owner_entity.name if owner_entity else series.entity_id
        opportunities.append(
            Opportunity(
                id=f"opp-efficiency-{series.entity_id}-{series.metric}",
                title=f"Lock in efficiency gains in {name}",
                reason=(
                    f"{name}: {series.metric.replace('_', ' ')} is improving "
                    f"({forecast.contributing_factors[0]}), freeing operational headroom."
                ),
                value_estimate=0.0,
                unit="capacity",
                confidence=forecast.confidence,
                priority=Priority.MEDIUM,
                owner=owner,
                action="Redirect the freed maintenance capacity to under-served areas and document the winning practice.",
                evidence=[
                    Evidence(label="Trend", value=", ".join(forecast.contributing_factors), source="forecast"),
                ],
            )
        )

    opportunities.sort(key=lambda o: (o.value_estimate, o.confidence), reverse=True)
    return opportunities
