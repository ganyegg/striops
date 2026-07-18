"""Agent protocol, shared context, and registry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from striops.core.models import (
    AgentContribution,
    BudgetLine,
    Entity,
    MetricSeries,
)
from striops.reasoning import LLMProvider


@dataclass
class AgentContext:
    """Everything an agent needs to reason. Shared, read-only across agents."""

    service_areas: list[Entity]
    metric_series: list[MetricSeries]
    budget_lines: list[BudgetLine]
    wards: list[Entity] = field(default_factory=list)
    llm: LLMProvider | None = None
    municipality: str = "Cape Town"


class Agent(ABC):
    """A specialist that contributes independent reasoning to the brief."""

    name: str = "agent"
    role: str = "specialist"

    @abstractmethod
    def analyze(self, ctx: AgentContext) -> AgentContribution: ...

    def _narrate(self, ctx: AgentContext, prompt: str, fallback: str) -> str:
        if ctx.llm is None:
            return fallback
        try:
            text = ctx.llm.generate(prompt, system=f"You are the {self.name} of Striops, an AI executive for {ctx.municipality}. Be concise, factual, and decision-oriented.")
            return text or fallback
        except Exception:
            return fallback


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> Agent | None:
        return self._agents.get(name)

    def all(self) -> list[Agent]:
        return list(self._agents.values())


default_registry = AgentRegistry()
