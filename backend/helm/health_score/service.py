"""Strategic health score — deterministic formula with full provenance."""
from __future__ import annotations

from pydantic import BaseModel, Field

from helm.core.models import Opportunity, Risk
from helm.opportunity_engine import find_opportunities
from helm.persistence import get_repository
from helm.risk_engine import assess_risks
from helm.valuation import attach_valuations

RISK_WEIGHT = 0.16
RISK_CAP = 55.0
OPP_UNIT_BONUS = 2.5
OPP_CAP = 8.0


class RiskContribution(BaseModel):
    risk_id: str
    title: str
    score: float
    weight: float = RISK_WEIGHT
    contribution: float
    href: str
    rank: int


class OpportunityContribution(BaseModel):
    opportunity_id: str
    title: str
    value_estimate: float
    qualifies: bool
    contribution: float
    href: str


class HealthBreakdown(BaseModel):
    base: float = 100.0
    risk_weight: float = RISK_WEIGHT
    risk_cap: float = RISK_CAP
    opportunity_unit_bonus: float = OPP_UNIT_BONUS
    opportunity_cap: float = OPP_CAP
    risk_lines: list[RiskContribution] = Field(default_factory=list)
    risk_penalty_raw: float
    risk_penalty_capped: float
    risk_cap_applied: bool
    opportunity_lines: list[OpportunityContribution] = Field(default_factory=list)
    opportunity_bonus_raw: float
    opportunity_bonus_capped: float
    opportunity_cap_applied: bool
    pre_round: float
    health_score: int
    health_narrative: str | None = None
    formula_plain_language: str
    engines_note: str = (
        "Engines compute this number from risk scores and valued opportunities. "
        "AI only writes the one-line narrative — it never sets the score."
    )


def compute_health_breakdown(
    risks: list[Risk],
    opportunities: list[Opportunity],
    *,
    health_narrative: str | None = None,
) -> HealthBreakdown:
    top = risks[:5]
    risk_lines: list[RiskContribution] = []
    raw_penalty = 0.0
    for i, r in enumerate(top, start=1):
        contrib = round(r.score * RISK_WEIGHT, 3)
        raw_penalty += contrib
        risk_lines.append(
            RiskContribution(
                risk_id=r.id,
                title=r.title,
                score=r.score,
                contribution=contrib,
                href=f"/risks/{r.id}",
                rank=i,
            )
        )
    raw_penalty = round(raw_penalty, 3)
    capped_penalty = min(RISK_CAP, raw_penalty)

    opp_lines: list[OpportunityContribution] = []
    raw_bonus = 0.0
    for o in opportunities:
        qualifies = o.value_estimate > 0
        contrib = OPP_UNIT_BONUS if qualifies else 0.0
        if qualifies:
            raw_bonus += contrib
        opp_lines.append(
            OpportunityContribution(
                opportunity_id=o.id,
                title=o.title,
                value_estimate=o.value_estimate,
                qualifies=qualifies,
                contribution=contrib,
                href="/#opportunities",
            )
        )
    raw_bonus = round(raw_bonus, 3)
    capped_bonus = min(OPP_CAP, raw_bonus)
    pre_round = round(100.0 - capped_penalty + capped_bonus, 3)
    score = int(max(0, min(100, round(pre_round))))

    formula = (
        f"100 − min({RISK_CAP:g}, Σ top-5 risk scores × {RISK_WEIGHT}) "
        f"+ min({OPP_CAP:g}, count(valued opportunities) × {OPP_UNIT_BONUS}) "
        f"= {pre_round} → {score}"
    )

    return HealthBreakdown(
        risk_lines=risk_lines,
        risk_penalty_raw=raw_penalty,
        risk_penalty_capped=capped_penalty,
        risk_cap_applied=raw_penalty > RISK_CAP,
        opportunity_lines=opp_lines,
        opportunity_bonus_raw=raw_bonus,
        opportunity_bonus_capped=capped_bonus,
        opportunity_cap_applied=raw_bonus > OPP_CAP,
        pre_round=pre_round,
        health_score=score,
        health_narrative=health_narrative,
        formula_plain_language=formula,
    )


def build_health_breakdown(municipality: str = "CPT") -> HealthBreakdown:
    """Full breakdown from the same risk/opportunity sets as the brief engines."""
    repo = get_repository()
    risks = assess_risks(repo.service_areas(), repo.metric_series(), repo.budget_lines())
    opps = find_opportunities(repo.service_areas(), repo.metric_series(), repo.budget_lines())
    risks, opps = attach_valuations(risks, opps, repo.metric_series(), municipality)
    risks = sorted(risks, key=lambda r: r.score, reverse=True)
    opps = sorted(opps, key=lambda o: (o.value_estimate, o.confidence), reverse=True)

    narrative = None
    try:
        from helm.core.cache import cache_get
        from helm.core.config import get_settings

        settings = get_settings()
        cached = cache_get(f"brief:{settings.helm_municipality}", settings.helm_brief_ttl_seconds)
        if cached is not None:
            narrative = cached.health_narrative
    except Exception:
        pass

    return compute_health_breakdown(risks, opps, health_narrative=narrative)
