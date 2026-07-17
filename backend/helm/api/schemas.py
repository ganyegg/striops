"""API request/response schemas that are not core domain models."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    function_name: str = Field(..., examples=["Solid Waste Management"])
    pct_change: float = Field(..., examples=[10], description="Percent change to the budget line")


class HealthResponse(BaseModel):
    status: str
    version: str
    facts_backend: str
    graph_nodes: int
    llm_provider: str


class EntitiesResponse(BaseModel):
    service_areas: list
    wards: list
    counts: dict
