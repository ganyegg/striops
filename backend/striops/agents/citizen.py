"""Citizen Agent — the resident experience of city services."""
from __future__ import annotations

from striops.agents.base import Agent, AgentContext
from striops.core.models import AgentContribution
from striops.opportunity_engine import find_opportunities

_CITIZEN_ENTITIES = {"svc-libraries", "svc-solid-waste"}


class CitizenAgent(Agent):
    name = "Citizen Agent"
    role = "Analyzes citizen experience"

    def analyze(self, ctx: AgentContext) -> AgentContribution:
        series = [s for s in ctx.metric_series if s.entity_id in _CITIZEN_ENTITIES]
        opportunities = [
            o for o in find_opportunities(ctx.service_areas, series, ctx.budget_lines) if o.unit != "ZAR"
        ]
        fallback = (
            "Citizen-facing services show mixed signals: rising complaints in waste collection alongside "
            "declining library engagement warrant a service-experience response."
        )
        prompt = "In 2 sentences, summarise the citizen experience for leadership."
        return AgentContribution(
            agent=self.name,
            summary=self._narrate(ctx, prompt, fallback),
            confidence=0.68,
            risks=[],
            opportunities=opportunities,
        )
