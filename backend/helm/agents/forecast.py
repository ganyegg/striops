"""Forecast Agent — where the numbers are heading."""
from __future__ import annotations

from helm.agents.base import Agent, AgentContext
from helm.core.models import AgentContribution, Trend
from helm.forecasting import forecast_series


class ForecastAgent(Agent):
    name = "Forecast Agent"
    role = "Predicts future trends"

    def analyze(self, ctx: AgentContext) -> AgentContribution:
        forecasts = [forecast_series(s) for s in ctx.metric_series]
        worsening = [f for f in forecasts if f.direction == Trend.WORSENING]
        improving = [f for f in forecasts if f.direction == Trend.IMPROVING]
        fallback = (
            f"{len(worsening)} metrics are on a worsening trajectory and {len(improving)} are improving. "
            "Trends are early enough to change with decisions taken now."
        )
        prompt = (
            "In 2 sentences, describe the emerging trends for the executive. "
            f"Forecasts: {[(f.metric, f.direction.value, f.contributing_factors[0]) for f in forecasts]}."
        )
        avg_conf = round(sum(f.confidence for f in forecasts) / len(forecasts), 3) if forecasts else 0.5
        return AgentContribution(
            agent=self.name,
            summary=self._narrate(ctx, prompt, fallback),
            confidence=avg_conf,
            risks=[],
            opportunities=[],
        )
