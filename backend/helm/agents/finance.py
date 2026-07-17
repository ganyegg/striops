"""Finance Agent — budget health and fiscal opportunities."""
from __future__ import annotations

from helm.agents.base import Agent, AgentContext
from helm.core.models import AgentContribution
from helm.opportunity_engine import find_opportunities


class FinanceAgent(Agent):
    name = "Finance Agent"
    role = "Analyzes budgets and financial health"

    def analyze(self, ctx: AgentContext) -> AgentContribution:
        opportunities = [
            o
            for o in find_opportunities(ctx.service_areas, ctx.metric_series, ctx.budget_lines)
            if o.unit == "ZAR"
        ]
        total_underspend = sum(o.value_estimate for o in opportunities)
        fallback = (
            f"Identified R{total_underspend / 1e9:.2f}bn of appropriated-but-unspent budget that can be "
            "redeployed to rising service demand this cycle without new funding."
            if opportunities
            else "Budgets are tracking close to plan; no material underspend to redeploy."
        )
        prompt = (
            "Summarise the municipality's fiscal position in 2 sentences for an executive. "
            f"Underspend opportunities: {[o.reason for o in opportunities]}."
        )
        return AgentContribution(
            agent=self.name,
            summary=self._narrate(ctx, prompt, fallback),
            confidence=0.75,
            risks=[],
            opportunities=opportunities,
        )
