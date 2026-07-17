"""Recommendation synthesis.

Pairs the highest-scoring risks with the best-matched opportunities to produce
explainable, evidence-backed decisions. A classic move: fund a rising risk with
an adjacent underspend rather than new money.
"""
from __future__ import annotations

from helm.core.models import (
    Evidence,
    Opportunity,
    Priority,
    Recommendation,
    Risk,
)


def _match_opportunity(risk: Risk, opportunities: list[Opportunity]) -> Opportunity | None:
    """Prefer an underspend opportunity owned by the same directorate."""
    same_owner = [o for o in opportunities if o.owner == risk.owner and o.value_estimate > 0]
    if same_owner:
        return same_owner[0]
    funded = [o for o in opportunities if o.value_estimate > 0]
    return funded[0] if funded else None


def recommend(
    risks: list[Risk],
    opportunities: list[Opportunity],
    limit: int = 4,
) -> list[Recommendation]:
    recs: list[Recommendation] = []
    for risk in risks[:limit]:
        opp = _match_opportunity(risk, opportunities)
        evidence: list[Evidence] = list(risk.evidence[:2])
        linked_opp_ids: list[str] = []
        if opp:
            evidence.append(
                Evidence(
                    label="Funding source",
                    value=f"{opp.title} (R{opp.value_estimate / 1e9:.2f}bn)"
                    if opp.value_estimate
                    else opp.title,
                    source="opportunity_engine",
                )
            )
            linked_opp_ids.append(opp.id)
            rationale = (
                f"{risk.reason} Fund the response from {opp.title.lower()} instead of new budget, "
                "keeping the intervention fiscally neutral."
            )
            expected = (
                f"Slows the {risk.title.lower()} trajectory while deploying idle funds already appropriated."
            )
        else:
            rationale = (
                f"{risk.reason} Act now while the trend is early and mitigation cost is lowest."
            )
            expected = f"Reduces likelihood and impact of {risk.title.lower()} before it compounds."

        recs.append(
            Recommendation(
                id=f"rec-{risk.id}",
                title=f"Act on: {risk.title}",
                rationale=rationale,
                confidence=round(min(0.95, 0.5 * risk.confidence + 0.4 + (0.05 if opp else 0)), 3),
                priority=risk.priority if risk.priority != Priority.LOW else Priority.MEDIUM,
                expected_impact=expected,
                evidence=evidence,
                linked_risk_ids=[risk.id],
                linked_opportunity_ids=linked_opp_ids,
            )
        )
    return recs
