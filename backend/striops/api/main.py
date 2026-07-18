"""Striops FastAPI application — Strategic Intelligence Operating System."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from striops import __version__
from striops.actions import Action, ActionRegister, build_action_register, get_action
from striops.agents import default_registry
from striops.api.schemas import (
    EntitiesResponse,
    HealthResponse,
    SimulationRequest,
)
from striops.ask import AskRequest, AskResponse, ask_striops
from striops.comparatives import ComparativesReport, build_comparatives
from striops.core.config import get_settings
from striops.core.glossary import GLOSSARY, explain, explain_risk_id
from striops.core.logging import configure_logging, get_logger
from striops.core.models import (
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
from striops.decisions import DecisionRegister, build_decision_register
from striops.demographics import attach_affected
from striops.domains import (
    domain_catalog,
    get_domain,
    get_municipality,
    list_domains,
    list_municipalities,
)
from striops.executive_brief import build_executive_brief
from striops.feeds import FeedsReport, build_feeds_report
from striops.health_score import HealthBreakdown, build_health_breakdown
from striops.knowledge_graph import get_graph_store
from striops.opportunity_engine import find_opportunities
from striops.persistence import get_repository
from striops.pulse import CityPulse, build_city_pulse
from striops.reasoning import get_llm
from striops.refresh import RefreshResult, run_refresh
from striops.reports import build_indicator_report, build_metric_report, build_risk_report
from striops.risk_engine import assess_risks
from striops.sectors import SectorsReport, build_sectors_report
from striops.simulation import list_scenarios, simulate
from striops.snapshot import build_city_snapshot
from striops.valuation import attach_valuations, valuation_catalog
from striops.value_ledger import ValueLedger, build_value_ledger
from striops.wins import build_initiative_report, list_initiatives

settings = get_settings()
configure_logging(settings.striops_log_level)
log = get_logger("striops.api")

app = FastAPI(
    title="Striops",
    description="Strategic Intelligence Operating System — Strategic Twin for Cities.",
    version=__version__,
)

# Best-effort: create the Postgres schema on boot so a freshly-provisioned
# managed database is immediately readable/writable (falls back to seed if
# Postgres is unavailable — never blocks startup).
try:
    from striops.persistence.schema import ensure_schema

    ensure_schema(settings)
except Exception as exc:  # pragma: no cover
    log.warning("startup schema bootstrap skipped", extra={"context": {"error": str(exc)}})

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
    assessed = assess_risks(repo.service_areas(), repo.metric_series(), repo.budget_lines())
    enriched, _ = attach_valuations(assessed, [], repo.metric_series(), settings.striops_municipality)
    return attach_affected(enriched, settings.striops_municipality)


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
    return build_city_snapshot(settings.striops_municipality)


@app.get("/health-breakdown", response_model=HealthBreakdown, tags=["intelligence"])
def health_breakdown() -> HealthBreakdown:
    return build_health_breakdown(settings.striops_municipality)


@app.get("/comparatives", response_model=ComparativesReport, tags=["intelligence"])
def comparatives() -> ComparativesReport:
    return build_comparatives(municipality=settings.striops_municipality)


@app.get("/sectors", response_model=SectorsReport, tags=["intelligence"])
def sectors() -> SectorsReport:
    """Critical sector spine with readiness and demographic denominators."""
    return build_sectors_report(settings.striops_municipality)


@app.post("/ask", response_model=AskResponse, tags=["intelligence"])
def ask(req: AskRequest) -> AskResponse:
    return ask_striops(req, settings=settings)


@app.post("/refresh", response_model=RefreshResult, tags=["system"])
def refresh(run_ingest: bool = True) -> RefreshResult:
    """Clear caches and re-pull public feeds so new data surfaces immediately."""
    return run_refresh(settings=settings, run_ingest=run_ingest)


@app.get("/wins", response_model=list[Initiative], tags=["wins"])
def wins() -> list[Initiative]:
    return list_initiatives(settings.striops_municipality)


@app.get("/wins/{initiative_id}", response_model=InitiativeReport, tags=["wins"])
def win_report(initiative_id: str) -> InitiativeReport:
    try:
        return build_initiative_report(settings.striops_municipality, initiative_id)
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
    return build_decision_register(settings.striops_municipality)


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
    opps = find_opportunities(repo.service_areas(), repo.metric_series(), repo.budget_lines())
    _, enriched = attach_valuations([], opps, repo.metric_series(), settings.striops_municipality)
    return enriched


@app.get("/actions", response_model=ActionRegister, tags=["intelligence"])
def actions() -> ActionRegister:
    return build_action_register(settings.striops_municipality)


@app.get("/actions/{action_id}", response_model=Action, tags=["intelligence"])
def action_detail(action_id: str) -> Action:
    action = get_action(settings.striops_municipality, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Unknown action: {action_id}")
    return action


@app.get("/value-ledger", response_model=ValueLedger, tags=["intelligence"])
def value_ledger() -> ValueLedger:
    return build_value_ledger(settings.striops_municipality)


@app.get("/valuation", tags=["intelligence"])
def valuation() -> dict:
    return valuation_catalog(settings.striops_municipality)


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
