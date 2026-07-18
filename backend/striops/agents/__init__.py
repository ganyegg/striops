"""Multi-agent reasoning layer.

Each specialist agent reasons independently over the shared context and returns
an `AgentContribution`. The `ExecutiveAgent` merges them into a single briefing.
The LLM narrates; the engines decide.
"""
from striops.agents.base import Agent, AgentContext, AgentRegistry, default_registry
from striops.agents.citizen import CitizenAgent
from striops.agents.executive import ExecutiveAgent
from striops.agents.finance import FinanceAgent
from striops.agents.forecast import ForecastAgent
from striops.agents.infrastructure import InfrastructureAgent
from striops.agents.risk import RiskAgent
from striops.agents.stubs import RecommendationAgent, SimulationAgent, StrategyAgent

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
