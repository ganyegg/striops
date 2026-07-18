"""Infrastructure Agent — assets, networks and service reliability."""
from __future__ import annotations

from striops.agents.base import Agent, AgentContext
from striops.core.models import AgentContribution
from striops.risk_engine import assess_risks

_INFRA_ENTITIES = {"svc-water", "svc-roads", "svc-lighting", "svc-solid-waste"}


class InfrastructureAgent(Agent):
    name = "Infrastructure Agent"
    role = "Monitors assets and infrastructure"

    def analyze(self, ctx: AgentContext) -> AgentContribution:
        series = [s for s in ctx.metric_series if s.entity_id in _INFRA_ENTITIES]
        risks = assess_risks(ctx.service_areas, series, ctx.budget_lines)
        worst = risks[0].title.lower() if risks else "no material infrastructure risk"
        fallback = (
            f"Infrastructure reliability is under pressure; the most urgent exposure is {worst}. "
            "Networks are degrading faster than current maintenance cadence can absorb."
            if risks
            else "Infrastructure networks are stable across monitored assets."
        )
        prompt = (
            "In 2 sentences, brief the executive on infrastructure risk. "
            f"Risks: {[r.reason for r in risks]}."
        )
        return AgentContribution(
            agent=self.name,
            summary=self._narrate(ctx, prompt, fallback),
            confidence=0.72,
            risks=risks,
            opportunities=[],
        )
