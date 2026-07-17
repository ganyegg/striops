"""Helm FastAPI application — Strategic Intelligence Operating System."""
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
from helm.core.glossary import GLOSSARY, explain, explain_risk_id
from helm.core.logging import configure_logging, get_logger
from helm.core.models import (
    CitySnapshot,
    DomainCatalogEntry,
    DomainProfile,
    ExecutiveBrief,
    IndicatorReport,
    Initiative,
    InitiativeReport,
    MetricReport,
    Municipality,
    Opportunity,
    Risk,
    RiskReport,
    SimulationResult,
)
from helm.decisions import DecisionRegister, build_decision_register
from helm.domains import (
    domain_catalog,
    get_domain,
    get_municipality,
    list_domains,
    list_municipalities,
)
from helm.executive_brief import build_executive_brief
from helm.feeds import FeedsReport, build_feeds_report
from helm.knowledge_graph import get_graph_store
from helm.opportunity_engine import find_opportunities
from helm.persistence import get_repository
from helm.pulse import CityPulse, build_city_pulse
from helm.reasoning import get_llm
from helm.reports import build_indicator_report, build_metric_report, build_risk_report
from helm.risk_engine import assess_risks
from helm.simulation import list_scenarios, simulate
from helm.snapshot import build_city_snapshot
from helm.wins import build_initiative_report, list_initiatives

settings = get_settings()
configure_logging(settings.helm_log_level)
log = get_logger("helm.api")

app = FastAPI(
    title="Helm",
    description="Strategic Intelligence Operating System — Strategic Twin for Cities.",
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


@app.get("/risks/{risk_id}", response_model=RiskReport, tags=["reports"])
def risk_report(risk_id: str) -> RiskReport:
    try:
        return build_risk_report(risk_id, repo=get_repository(settings))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/metrics/{entity_id}/{metric}", response_model=MetricReport, tags=["reports"])
def metric_report(entity_id: str, metric: str) -> MetricReport:
    try:
        return build_metric_report(entity_id, metric, repo=get_repository(settings))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/municipalities/{code}/domains/{domain_id}/indicators/{indicator_key}",
    response_model=IndicatorReport,
    tags=["reports"],
)
def indicator_report(code: str, domain_id: str, indicator_key: str) -> IndicatorReport:
    try:
        return build_indicator_report(code, domain_id, indicator_key, repo=get_repository(settings))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/snapshot", response_model=CitySnapshot, tags=["intelligence"])
def snapshot() -> CitySnapshot:
    return build_city_snapshot(settings.helm_municipality)


@app.get("/wins", response_model=list[Initiative], tags=["wins"])
def wins() -> list[Initiative]:
    return list_initiatives(settings.helm_municipality)


@app.get("/wins/{initiative_id}", response_model=InitiativeReport, tags=["wins"])
def win_report(initiative_id: str) -> InitiativeReport:
    try:
        return build_initiative_report(settings.helm_municipality, initiative_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/pulse", response_model=CityPulse, tags=["intelligence"])
def pulse() -> CityPulse:
    return build_city_pulse(repo=get_repository(settings), settings=settings)


@app.get("/feeds", response_model=FeedsReport, tags=["system"])
def feeds() -> FeedsReport:
    return build_feeds_report(repo=get_repository(settings), settings=settings)


@app.get("/decisions", response_model=DecisionRegister, tags=["intelligence"])
def decisions() -> DecisionRegister:
    return build_decision_register(settings.helm_municipality)


@app.get("/glossary", tags=["intelligence"])
def glossary() -> dict:
    return GLOSSARY


@app.get("/glossary/{key}", tags=["intelligence"])
def glossary_key(key: str) -> dict:
    entry = explain(key) or explain_risk_id(key)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Unknown glossary key: {key}")
    return entry


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
