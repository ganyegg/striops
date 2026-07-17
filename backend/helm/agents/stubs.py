"""Declared-but-not-yet-active agents from the full vision roster.

They are registered so the multi-agent roster is complete and discoverable, and
are activated in later phases (Board Meeting Mode, continuous strategy, etc.).
"""
from __future__ import annotations

from helm.agents.base import Agent, AgentContext
from helm.core.models import AgentContribution


class _DeclaredAgent(Agent):
    def analyze(self, ctx: AgentContext) -> AgentContribution:
        return AgentContribution(
            agent=self.name,
            summary=f"{self.name} declared ({self.role}); activates in a later phase.",
            confidence=0.0,
        )


class SimulationAgent(_DeclaredAgent):
    name = "Simulation Agent"
    role = "Runs What-If scenarios"


class StrategyAgent(_DeclaredAgent):
    name = "Strategy Agent"
    role = "Finds long-term opportunities"


class RecommendationAgent(_DeclaredAgent):
    name = "Recommendation Agent"
    role = "Produces final recommendations"
