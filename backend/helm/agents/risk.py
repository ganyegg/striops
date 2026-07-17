"""Risk Agent — authoritative, cross-cutting strategic risk view."""
from __future__ import annotations

from helm.agents.base import Agent, AgentContext
from helm.core.models import AgentContribution
from helm.risk_engine import assess_risks


class RiskAgent(Agent):
    name = "Risk Agent"
    role = "Identifies strategic risks"

    def analyze(self, ctx: AgentContext) -> AgentContribution:
        risks = assess_risks(ctx.service_areas, ctx.metric_series, ctx.budget_lines)
        critical = [r for r in risks if r.priority.value in ("critical", "high")]
        fallback = (
            f"{len(risks)} active strategic risks, {len(critical)} at high or critical priority. "
            f"Top exposure: {risks[0].title.lower()} (score {risks[0].score})."
            if risks
            else "No active strategic risks detected across monitored domains."
        )
        prompt = (
            "Summarise the strategic risk posture in 2 sentences for leadership. "
            f"Ranked risks: {[(r.title, r.score) for r in risks]}."
        )
        avg_conf = round(sum(r.confidence for r in risks) / len(risks), 3) if risks else 0.6
        return AgentContribution(
            agent=self.name,
            summary=self._narrate(ctx, prompt, fallback),
            confidence=avg_conf,
            risks=risks,
            opportunities=[],
        )
