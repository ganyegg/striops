"""Shared domain models.

These are the vocabulary of Helm's reasoning core. They are deliberately
independent of any datastore so engines and agents can be unit-tested in
isolation with hand-built inputs (no DB required).
"""
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class EntityType(str, Enum):
    WARD = "Ward"
    DEPARTMENT = "Department"
    BUDGET_ITEM = "BudgetItem"
    ASSET = "Asset"
    SERVICE_AREA = "ServiceArea"
    INFRASTRUCTURE = "Infrastructure"
    PROJECT = "Project"


class MetricPoint(BaseModel):
    period: date
    value: float


class MetricSeries(BaseModel):
    entity_id: str
    metric: str
    unit: str | None = None
    points: list[MetricPoint] = Field(default_factory=list)

    def values(self) -> list[float]:
        return [p.value for p in sorted(self.points, key=lambda p: p.period)]


class Entity(BaseModel):
    id: str
    type: EntityType
    name: str
    properties: dict = Field(default_factory=dict)
    relationships: list[dict] = Field(default_factory=list)


class BudgetLine(BaseModel):
    function_name: str
    financial_year: int
    budget: float
    actual: float
    source: str | None = None

    @property
    def variance(self) -> float:
        """Positive => underspend (spent less than budgeted)."""
        return self.budget - self.actual

    @property
    def utilisation(self) -> float:
        if self.budget == 0:
            return 0.0
        return self.actual / self.budget


class Trend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"


class Forecast(BaseModel):
    entity_id: str
    metric: str
    direction: Trend
    slope: float
    projected_next: float
    confidence: float = Field(ge=0.0, le=1.0)
    contributing_factors: list[str] = Field(default_factory=list)


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Evidence(BaseModel):
    label: str
    value: str
    source: str | None = None


class CostEstimate(BaseModel):
    """Sourced annual cost / gain estimate attached to a risk or opportunity."""

    amount_zar: float
    basis: str  # e.g. "annual_cost_of_current_level" | "annual_cost_of_trend"
    method: str
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: list[dict] = Field(default_factory=list)
    unit_note: str | None = None


class AffectedPopulation(BaseModel):
    """Who is touched by a risk/issue — coarse, sourced, never invented."""

    population_estimate: float | None = None
    unit: str = "residents"  # residents | households | patients/month | …
    geography: str
    method: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_label: str | None = None
    source_url: str | None = None
    as_of: str | None = None
    gaps: list[str] = Field(default_factory=list)
    vulnerability_notes: list[str] = Field(default_factory=list)


class Risk(BaseModel):
    id: str
    title: str
    reason: str
    likelihood: float = Field(ge=0.0, le=1.0)
    impact: float = Field(ge=0.0, le=1.0)
    trend: float = Field(ge=0.0, le=2.0, description="Trend multiplier; >1 worsening")
    confidence: float = Field(ge=0.0, le=1.0)
    priority: Priority
    owner: str
    mitigation: str
    evidence: list[Evidence] = Field(default_factory=list)
    forecast: Forecast | None = None
    cost_estimate: CostEstimate | None = None
    affected: AffectedPopulation | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def score(self) -> float:
        """Risk = Likelihood x Impact x Trend x Confidence, scaled to 0-100."""
        return round(self.likelihood * self.impact * self.trend * self.confidence * 100, 1)


class Opportunity(BaseModel):
    id: str
    title: str
    reason: str
    value_estimate: float
    unit: str = "ZAR"
    confidence: float = Field(ge=0.0, le=1.0)
    priority: Priority
    owner: str
    action: str
    evidence: list[Evidence] = Field(default_factory=list)
    gain_estimate: CostEstimate | None = None


class Recommendation(BaseModel):
    id: str
    title: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    priority: Priority
    expected_impact: str
    evidence: list[Evidence] = Field(default_factory=list)
    linked_risk_ids: list[str] = Field(default_factory=list)
    linked_opportunity_ids: list[str] = Field(default_factory=list)


class AgentContribution(BaseModel):
    agent: str
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    risks: list[Risk] = Field(default_factory=list)
    opportunities: list[Opportunity] = Field(default_factory=list)


class ExecutiveBrief(BaseModel):
    greeting: str
    generated_for: str
    health_score: int = Field(ge=0, le=100)
    health_narrative: str
    strategic_summary: str
    top_risks: list[Risk] = Field(default_factory=list)
    top_opportunities: list[Opportunity] = Field(default_factory=list)
    recommended_decisions: list[Recommendation] = Field(default_factory=list)
    emerging_trends: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    agent_contributions: list[AgentContribution] = Field(default_factory=list)


class ScenarioImpact(BaseModel):
    dimension: str  # financial | operational | citizen | environmental | political | risk
    delta: str
    detail: str
    confidence: float = Field(ge=0.0, le=1.0)


class Scenario(BaseModel):
    name: str
    description: str
    impacts: list[ScenarioImpact] = Field(default_factory=list)


class SimulationResult(BaseModel):
    question: str
    baseline: Scenario
    scenario: Scenario
    recommended: str
    recommendation_detail: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Drill-down reports (risks / metrics) — full narrative + series + sources
# --------------------------------------------------------------------------


class ScoreBreakdown(BaseModel):
    likelihood: float
    impact: float
    trend: float
    confidence: float
    score: float
    formula: str = "Likelihood × Impact × Trend × Confidence × 100"


class MetricStats(BaseModel):
    latest: float
    previous: float | None = None
    change: float | None = None
    change_pct: float | None = None
    period_start: str | None = None
    period_end: str | None = None
    n_points: int = 0
    min_value: float | None = None
    max_value: float | None = None
    mean: float | None = None


class ChartPoint(BaseModel):
    period: str
    value: float
    kind: str = "actual"  # actual | projected


class ReferenceLink(BaseModel):
    label: str
    publisher: str
    url: str
    as_of: str | None = None
    note: str | None = None


class MetricReport(BaseModel):
    entity_id: str
    entity_name: str
    metric: str
    metric_label: str
    unit: str | None = None
    series: list[ChartPoint] = Field(default_factory=list)
    projected: list[ChartPoint] = Field(default_factory=list)
    forecast: Forecast | None = None
    stats: MetricStats
    owner: str | None = None
    department: str | None = None
    related_domain_id: str | None = None
    related_risk_id: str | None = None
    narrative: str
    references: list[ReferenceLink] = Field(default_factory=list)


class RiskReport(BaseModel):
    risk: Risk
    score_breakdown: ScoreBreakdown
    metric_report: MetricReport | None = None
    related_domain_id: str | None = None
    related_budget_function: str | None = None
    narrative: str
    what_changed: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    references: list[ReferenceLink] = Field(default_factory=list)
    plain_language: str | None = None
    term: str | None = None
    in_one_line: str | None = None


# --------------------------------------------------------------------------
# Deep-dive domain profiles + provenance
# Every published number carries a resolvable source so a councillor or
# journalist can verify it. Provenance travels with the data.
# --------------------------------------------------------------------------


class DomainId(str, Enum):
    FISCAL = "fiscal"
    BUDGET = "budget"
    STAFFING = "staffing"
    HOUSING_POPULATION = "housing_population"
    SAFETY_POLICING = "safety_policing"
    GOVERNANCE_POLICIES = "governance_policies"
    WATER = "water"
    ENERGY = "energy"
    WASTE = "waste"
    TRANSPORT = "transport"
    ECONOMY_JOBS = "economy_jobs"
    HEALTH = "health"
    ENVIRONMENT = "environment"
    SERVICE_DELIVERY = "service_delivery"


class IndicatorTrend(str, Enum):
    UP = "up"
    DOWN = "down"
    FLAT = "flat"
    NA = "na"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"  # cross-checked against the cited public source
    NEEDS_VERIFICATION = "needs_verification"  # sourced but not yet re-checked
    ESTIMATE = "estimate"  # modelled/derived, not a published figure


class Source(BaseModel):
    id: str
    publisher: str
    title: str
    url: str
    retrieved_at: date | None = None
    license: str | None = None
    coverage: str | None = None  # e.g. "City of Cape Town, 2026/27"


class Indicator(BaseModel):
    key: str
    label: str
    value: str  # display-ready (already formatted, e.g. "R87.79bn")
    numeric: float | None = None
    unit: str | None = None
    as_of: str  # human-readable period, e.g. "2026/27 budget"
    trend: IndicatorTrend = IndicatorTrend.NA
    trend_note: str | None = None
    verification: VerificationStatus = VerificationStatus.NEEDS_VERIFICATION
    method: str | None = None  # how it was derived, if not a direct figure
    source_id: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class Policy(BaseModel):
    title: str
    status: str  # e.g. "Adopted", "In force", "Proposed"
    as_of: str
    detail: str
    source_id: str


class DomainProfile(BaseModel):
    id: DomainId
    name: str
    municipality: str
    summary: str
    indicators: list[Indicator] = Field(default_factory=list)
    policies: list[Policy] = Field(default_factory=list)
    watchpoints: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    last_updated: str | None = None
    coverage_note: str | None = None

    @property
    def verified_share(self) -> float:
        if not self.indicators:
            return 0.0
        v = sum(1 for i in self.indicators if i.verification == VerificationStatus.VERIFIED)
        return round(v / len(self.indicators), 3)


class DomainCatalogEntry(BaseModel):
    id: DomainId
    name: str
    description: str
    icon: str  # icon key for the frontend
    order: int = 100


class Municipality(BaseModel):
    code: str
    name: str
    province: str
    category: str  # "metro" | "local" | "district"
    seat: str | None = None
    population: str | None = None
    wards: int | None = None
    status: str = "planned"  # "live" | "in_progress" | "planned"
    data_sources: dict = Field(default_factory=dict)
    domains_available: list[DomainId] = Field(default_factory=list)


class IndicatorReport(BaseModel):
    municipality_code: str
    municipality_name: str
    domain_id: str
    domain_name: str
    indicator: Indicator
    source: Source | None = None
    domain_summary: str
    watchpoints: list[str] = Field(default_factory=list)
    related_indicators: list[Indicator] = Field(default_factory=list)
    related_risk_ids: list[str] = Field(default_factory=list)
    related_metric: dict | None = None  # {entity_id, metric} if linked
    narrative: str
    references: list[ReferenceLink] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Wins / Initiatives — the other half of an honest executive briefing
# --------------------------------------------------------------------------


class WinMetric(BaseModel):
    label: str
    value: str
    as_of: str
    source_id: str


class Initiative(BaseModel):
    id: str
    title: str
    headline: str
    plain_language: str
    why_it_matters: str
    category: str
    status: str
    priority: Priority
    confidence: float = Field(ge=0.0, le=1.0)
    owner: str
    image_url: str | None = None
    image_credit: str | None = None
    metrics: list[WinMetric] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    next_step: str
    related_domain_id: str | None = None
    related_risk_ids: list[str] = Field(default_factory=list)
    related_metric: dict | None = None
    source_ids: list[str] = Field(default_factory=list)


class InitiativeReport(BaseModel):
    initiative: Initiative
    sources: list[Source] = Field(default_factory=list)
    references: list[ReferenceLink] = Field(default_factory=list)
    narrative: str
    metric_report: MetricReport | None = None


class HeroKPI(BaseModel):
    key: str
    label: str
    value: str
    hint: str
    tone: str  # good | warn | bad | neutral
    href: str | None = None
    plain_language: str | None = None


class CitySnapshot(BaseModel):
    """Mayor-facing top-of-brief numbers — verifiable, sparse, high-signal."""

    municipality: str
    greeting: str
    tagline: str
    health_score: int
    health_narrative: str | None = None
    kpis: list[HeroKPI] = Field(default_factory=list)
    confidence_note: str
    data_through: str | None = None  # e.g. "February 2026"
    previous_period: str | None = None  # e.g. "January 2026"
    generated_at: str | None = None  # ISO timestamp of brief/snapshot build
    brief_refreshed_at: str | None = None
