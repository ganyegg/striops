"""Helm AI FastAPI application."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from helm import __version__
from helm.agents import default_registry
from helm.api.schemas import (
    EntitiesResponse,
    HealthResponse,
    SimulationRequest,
)
from helm.core.config import get_settings
from helm.core.logging import configure_logging, get_logger
from helm.core.models import (
    DomainCatalogEntry,
    DomainProfile,
    ExecutiveBrief,
    Municipality,
    Opportunity,
    Risk,
    SimulationResult,
)
from helm.domains import (
    domain_catalog,
    get_domain,
    get_municipality,
    list_domains,
    list_municipalities,
)
from helm.executive_brief import build_executive_brief
from helm.knowledge_graph import get_graph_store
from helm.opportunity_engine import find_opportunities
from helm.persistence import get_repository
from helm.reasoning import get_llm
from helm.risk_engine import assess_risks
from helm.simulation import list_scenarios, simulate

settings = get_settings()
configure_logging(settings.helm_log_level)
log = get_logger("helm.api")

app = FastAPI(
    title="Helm AI",
    description="Strategic Intelligence Operating System — AI Strategic Twin for Cities.",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    repo = get_repository(settings)
    try:
        graph_nodes = get_graph_store(settings).count()
    except Exception:
        graph_nodes = 0
    return HealthResponse(
        status="ok",
        version=__version__,
        facts_backend=repo.backend,
        graph_nodes=graph_nodes,
        llm_provider=get_llm(settings).name,
    )


@app.get("/brief", response_model=ExecutiveBrief, tags=["intelligence"])
def brief() -> ExecutiveBrief:
    return build_executive_brief(settings=settings)


@app.get("/risks", response_model=list[Risk], tags=["intelligence"])
def risks() -> list[Risk]:
    repo = get_repository(settings)
    return assess_risks(repo.service_areas(), repo.metric_series(), repo.budget_lines())


@app.get("/opportunities", response_model=list[Opportunity], tags=["intelligence"])
def opportunities() -> list[Opportunity]:
    repo = get_repository(settings)
    return find_opportunities(repo.service_areas(), repo.metric_series(), repo.budget_lines())


@app.get("/entities", response_model=EntitiesResponse, tags=["strategic-twin"])
def entities() -> EntitiesResponse:
    repo = get_repository(settings)
    sa = repo.service_areas()
    wards = repo.wards()
    return EntitiesResponse(
        service_areas=[e.model_dump() for e in sa],
        wards=[e.model_dump() for e in wards],
        counts={"service_areas": len(sa), "wards": len(wards)},
    )


@app.get("/simulate/scenarios", tags=["simulation"])
def scenarios() -> list[dict]:
    return list_scenarios(get_repository(settings))


@app.post("/simulate", response_model=SimulationResult, tags=["simulation"])
def run_simulation(req: SimulationRequest) -> SimulationResult:
    try:
        return simulate(req.function_name, req.pct_change, repo=get_repository(settings), llm=get_llm(settings))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/agents", tags=["system"])
def agents() -> list[dict]:
    return [{"name": a.name, "role": a.role} for a in default_registry.all()]


# --------------------------------------------------------------------------
# Municipalities + deep-dive domain profiles (provenance-first)
# --------------------------------------------------------------------------


@app.get("/domains/catalog", response_model=list[DomainCatalogEntry], tags=["domains"])
def domains_catalog() -> list[DomainCatalogEntry]:
    return domain_catalog()


@app.get("/municipalities", response_model=list[Municipality], tags=["municipalities"])
def municipalities() -> list[Municipality]:
    return list_municipalities()


@app.get("/municipalities/{code}", response_model=Municipality, tags=["municipalities"])
def municipality(code: str) -> Municipality:
    muni = get_municipality(code)
    if muni is None:
        raise HTTPException(status_code=404, detail=f"Unknown municipality: {code}")
    return muni


@app.get("/municipalities/{code}/domains", tags=["domains"])
def municipality_domains(code: str) -> list[dict]:
    if get_municipality(code) is None:
        raise HTTPException(status_code=404, detail=f"Unknown municipality: {code}")
    return list_domains(code)


@app.get("/municipalities/{code}/domains/{domain_id}", response_model=DomainProfile, tags=["domains"])
def municipality_domain(code: str, domain_id: str) -> DomainProfile:
    if get_municipality(code) is None:
        raise HTTPException(status_code=404, detail=f"Unknown municipality: {code}")
    try:
        return get_domain(code, domain_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
