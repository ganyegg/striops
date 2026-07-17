"""Assemble the morning Executive Brief from the multi-agent pipeline."""
from __future__ import annotations

from datetime import datetime

from helm.agents import SPECIALIST_AGENTS, AgentContext, ExecutiveAgent
from helm.core.cache import cache_get, cache_set
from helm.core.config import Settings, get_settings
from helm.core.logging import get_logger
from helm.core.models import (
    ExecutiveBrief,
    Opportunity,
    Risk,
    Trend,
)
from helm.forecasting import forecast_series
from helm.persistence import Repository, get_repository
from helm.reasoning import get_llm
from helm.recommendation_engine import recommend
from helm.valuation import attach_valuations

log = get_logger("helm.executive_brief")

_MUNICIPALITY_NAMES = {"CPT": "Cape Town"}


def _greeting(city: str) -> str:
    hour = datetime.now().hour
    part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    return f"Good {part}, {city}."


def _dedupe_risks(risks: list[Risk]) -> list[Risk]:
    seen: dict[str, Risk] = {}
    for r in risks:
        if r.id not in seen or r.score > seen[r.id].score:
            seen[r.id] = r
    return sorted(seen.values(), key=lambda r: r.score, reverse=True)


def _dedupe_opportunities(opps: list[Opportunity]) -> list[Opportunity]:
    seen: dict[str, Opportunity] = {}
    for o in opps:
        seen[o.id] = o
    return sorted(seen.values(), key=lambda o: (o.value_estimate, o.confidence), reverse=True)


def _health_score(risks: list[Risk], opportunities: list[Opportunity]) -> int:
    from helm.health_score import compute_health_breakdown

    return compute_health_breakdown(risks, opportunities).health_score


def build_executive_brief(
    repo: Repository | None = None,
    settings: Settings | None = None,
) -> ExecutiveBrief:
    settings = settings or get_settings()
    repo = repo or get_repository(settings)
    llm = get_llm(settings)
    city = _MUNICIPALITY_NAMES.get(settings.helm_municipality, settings.helm_municipality)

    # The brief is expensive (a dozen LLM calls); serve a cached copy within
    # the TTL, refreshing only the time-of-day greeting.
    cache_key = f"brief:{settings.helm_municipality}"
    if settings.helm_brief_ttl_seconds > 0:
        cached = cache_get(cache_key, settings.helm_brief_ttl_seconds)
        if cached is not None:
            return cached.model_copy(update={"greeting": _greeting(city)})

    ctx = AgentContext(
        service_areas=repo.service_areas(),
        metric_series=repo.metric_series(),
        budget_lines=repo.budget_lines(),
        wards=repo.wards(),
        llm=llm,
        municipality=city,
    )

    contributions = [agent.analyze(ctx) for agent in SPECIALIST_AGENTS]

    all_risks: list[Risk] = []
    all_opps: list[Opportunity] = []
    for c in contributions:
        all_risks.extend(c.risks)
        all_opps.extend(c.opportunities)

    risks = _dedupe_risks(all_risks)
    opportunities = _dedupe_opportunities(all_opps)
    risks, opportunities = attach_valuations(
        risks, opportunities, ctx.metric_series, settings.helm_municipality
    )
    from helm.demographics import attach_affected

    risks = attach_affected(risks, settings.helm_municipality)
    recommendations = recommend(risks, opportunities)
    health = _health_score(risks, opportunities)

    # Emerging trends straight from the forecast engine (explainable).
    emerging: list[str] = []
    for series in ctx.metric_series:
        f = forecast_series(series)
        if f.direction == Trend.STABLE:
            continue
        arrow = "up" if f.slope > 0 else "down"
        emerging.append(
            f"{series.metric.replace('_', ' ').title()} trending {arrow} ({f.direction.value}, "
            f"{f.contributing_factors[0]})"
        )

    exec_agent = ExecutiveAgent()
    summary, health_narrative, confidence = exec_agent.synthesize(
        ctx, contributions, risks, opportunities, recommendations, health
    )

    log.info(
        "executive brief built",
        extra={"context": {"health": health, "risks": len(risks), "opps": len(opportunities), "backend": repo.backend}},
    )

    brief = ExecutiveBrief(
        greeting=_greeting(city),
        generated_for=city,
        health_score=health,
        health_narrative=health_narrative,
        strategic_summary=summary,
        top_risks=risks[:5],
        top_opportunities=opportunities[:5],
        recommended_decisions=recommendations,
        emerging_trends=emerging,
        confidence=confidence,
        agent_contributions=contributions,
    )
    if settings.helm_brief_ttl_seconds > 0:
        cache_set(cache_key, brief)
    return brief
