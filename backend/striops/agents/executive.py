"""Executive Agent — merges specialist reasoning into a single briefing."""
from __future__ import annotations

from striops.agents.base import Agent, AgentContext
from striops.core.models import (
    AgentContribution,
    Opportunity,
    Recommendation,
    Risk,
)


class ExecutiveAgent(Agent):
    name = "Executive Agent"
    role = "Creates executive briefings"

    def analyze(self, ctx: AgentContext) -> AgentContribution:  # pragma: no cover - not used directly
        return AgentContribution(agent=self.name, summary="Executive merge agent.", confidence=1.0)

    def synthesize(
        self,
        ctx: AgentContext,
        contributions: list[AgentContribution],
        risks: list[Risk],
        opportunities: list[Opportunity],
        recommendations: list[Recommendation],
        health_score: int,
    ) -> tuple[str, str, float]:
        """Return (strategic_summary, health_narrative, confidence)."""
        active = [c for c in contributions if c.confidence > 0]
        confidence = round(sum(c.confidence for c in active) / len(active), 3) if active else 0.6

        top_risk = risks[0].title.lower() if risks else "no material risk"
        top_opp = opportunities[0].title.lower() if opportunities else "no material opportunity"
        top_move = recommendations[0].title if recommendations else "hold current course"

        summary_fallback = (
            f"Strategic health for {ctx.municipality} stands at {health_score}/100. "
            f"The dominant risk is {top_risk}; the clearest opportunity is {top_opp}. "
            f"Leadership's highest-leverage move today: {top_move.lower()}."
        )
        health_fallback = (
            f"Health of {health_score}/100 reflects {len([r for r in risks if r.priority.value in ('critical', 'high')])} "
            f"high/critical risks balanced against {len(opportunities)} actionable opportunities."
        )

        prompt = (
            "You are briefing city leadership like a chief of staff briefs a president. "
            "Write a 3-sentence strategic summary that is calm, decisive and forward-looking. "
            f"Health score: {health_score}/100. "
            f"Specialist summaries: {[c.summary for c in active]}. "
            f"Top risks: {[r.title for r in risks[:3]]}. "
            f"Top opportunities: {[o.title for o in opportunities[:3]]}. "
            f"Recommended decisions: {[r.title for r in recommendations[:3]]}."
        )
        strategic_summary = self._narrate(ctx, prompt, summary_fallback)

        health_prompt = (
            f"In one sentence, explain what a strategic health score of {health_score}/100 means "
            f"given these risks {[r.title for r in risks[:3]]} and opportunities {[o.title for o in opportunities[:2]]}."
        )
        health_narrative = self._narrate(ctx, health_prompt, health_fallback)

        return strategic_summary, health_narrative, confidence
