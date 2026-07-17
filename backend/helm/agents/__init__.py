"""Multi-agent reasoning layer.

Each specialist agent reasons independently over the shared context and returns
an `AgentContribution`. The `ExecutiveAgent` merges them into a single briefing.
The LLM narrates; the engines decide.
"""
from helm.agents.base import Agent, AgentContext, AgentRegistry, default_registry
from helm.agents.citizen import CitizenAgent
from helm.agents.executive import ExecutiveAgent
from helm.agents.finance import FinanceAgent
from helm.agents.forecast import ForecastAgent
from helm.agents.infrastructure import InfrastructureAgent
from helm.agents.risk import RiskAgent
from helm.agents.stubs import RecommendationAgent, SimulationAgent, StrategyAgent

# Specialist agents that actively contribute to the brief.
SPECIALIST_AGENTS: list[Agent] = [
    FinanceAgent(),
    InfrastructureAgent(),
    RiskAgent(),
    ForecastAgent(),
    CitizenAgent(),
]

# Full roster (incl. declared-for-later agents) for discoverability.
for _agent in [*SPECIALIST_AGENTS, SimulationAgent(), StrategyAgent(), RecommendationAgent(), ExecutiveAgent()]:
    default_registry.register(_agent)

__all__ = [
    "Agent",
    "AgentContext",
    "AgentRegistry",
    "default_registry",
    "ExecutiveAgent",
    "SPECIALIST_AGENTS",
    "FinanceAgent",
    "InfrastructureAgent",
    "RiskAgent",
    "ForecastAgent",
    "CitizenAgent",
]
