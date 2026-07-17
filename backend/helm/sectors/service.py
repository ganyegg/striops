"""Critical sector spine — mayor-facing readiness, not equal dashboard tiles."""
from __future__ import annotations

from pydantic import BaseModel, Field

from helm.core.models import AffectedPopulation
from helm.demographics import domain_affected
from helm.domains import list_domains
from helm.persistence import get_repository
from helm.pulse import build_city_pulse
from helm.risk_engine import assess_risks
from helm.demographics import attach_affected
from helm.valuation import attach_valuations


class SectorMetricRef(BaseModel):
    entity_id: str
    metric: str
    label: str


class CriticalSector(BaseModel):
    id: str
    name: str
    priority: str  # P0 | P1 | P2 | P3
    domain_id: str | None = None
    href: str
    mayor_question: str
    ownership_note: str | None = None
    status: str  # improving | worsening | flat | mixed | unknown
    domain_available: bool = False
    ops_series_count: int = 0
    has_affected: bool = False
    headline: str | None = None
    blocker: str | None = None
    ask_prompt: str
    metrics: list[SectorMetricRef] = Field(default_factory=list)
    affected: AffectedPopulation | None = None
    top_risk_id: str | None = None
    top_risk_title: str | None = None


class SectorsReport(BaseModel):
    municipality: str
    note: str = (
        "Critical sectors are ordered for the mayor's room. Empty is not failure — "
        "empty is the data request. Libraries stay visible but never above Health, "
        "Safety, Housing, Water, or Energy."
    )
    sectors: list[CriticalSector] = Field(default_factory=list)
    p0_ready_count: int = 0
    p0_total: int = 0


# Spine definition — data-driven status filled at build time.
_SPINE: list[dict] = [
    {
        "id": "health",
        "name": "Health",
        "priority": "P0",
        "domain_id": "health",
        "mayor_question": "Are people waiting longer for care?",
        "ownership_note": (
            "City owns clinics & EMS. Acute hospitals are Western Cape DoH — "
            "linked externally; Helm will not invent hospital stats."
        ),
        "ask_prompt": "Brief me on City Health access — clinics and EMS — and who is affected.",
        "metrics": [
            ("svc-health", "clinic_waiting_days", "Clinic waiting days"),
            ("svc-health", "ems_response_minutes", "EMS response"),
        ],
        "blocker_if_empty": "Wire official City Health PHC waiting-time and EMS extracts.",
    },
    {
        "id": "water",
        "name": "Water & sanitation",
        "priority": "P0",
        "domain_id": "water",
        "mayor_question": "Will we make summer?",
        "ask_prompt": "Compare dam storage and non-revenue water — what should we do before summer?",
        "metrics": [
            ("svc-water", "dam_storage", "Dam storage"),
            ("svc-water", "non_revenue_water_pct", "Non-revenue water"),
        ],
        "blocker_if_empty": "Dam and NRW series missing from facts store.",
    },
    {
        "id": "safety",
        "name": "Safety & policing",
        "priority": "P0",
        "domain_id": "safety_policing",
        "mayor_question": "Is crime moving in LEAP areas?",
        "ask_prompt": "What do we know about safety and LEAP — and what is still unverified?",
        "metrics": [],
        "blocker_if_empty": "Attach verified SAPS quarter + precinct list before crime claims.",
    },
    {
        "id": "housing",
        "name": "Housing & population",
        "priority": "P0",
        "domain_id": "housing_population",
        "mayor_question": "Is the housing backlog growing?",
        "ask_prompt": "What is the housing backlog and delivery gap — who is on the list?",
        "metrics": [],
        "blocker_if_empty": "Publish monthly delivery vs budgeted units into Helm.",
    },
    {
        "id": "energy",
        "name": "Energy",
        "priority": "P0",
        "domain_id": "energy",
        "mayor_question": "Are we buffering residents from load-shedding?",
        "ask_prompt": "What is confirmed on energy and load-shedding protection?",
        "metrics": [],
        "blocker_if_empty": "Quantify buffered load-shedding stages with a sourced series.",
    },
    {
        "id": "transport",
        "name": "Roads & transport",
        "priority": "P1",
        "domain_id": "transport",
        "mayor_question": "Is mobility getting worse on key corridors?",
        "ask_prompt": "How is the road backlog trending and what does it mean for residents?",
        "metrics": [("svc-roads", "road_maintenance_backlog_km", "Road backlog")],
        "blocker_if_empty": "Road backlog series missing.",
    },
    {
        "id": "waste",
        "name": "Waste & cleansing",
        "priority": "P1",
        "domain_id": "waste",
        "mayor_question": "Why are refuse complaints rising?",
        "ask_prompt": "What is driving refuse service requests and who feels it?",
        "metrics": [("svc-solid-waste", "refuse_service_requests", "Refuse requests")],
        "blocker_if_empty": "Refuse series missing.",
    },
    {
        "id": "fiscal",
        "name": "Fiscal & budget",
        "priority": "P1",
        "domain_id": "budget",
        "mayor_question": "Can we afford the fix?",
        "ask_prompt": "What fiscal room do we have against the top risks?",
        "metrics": [],
        "blocker_if_empty": "Budget domain not loaded.",
    },
    {
        "id": "libraries",
        "name": "Libraries & community",
        "priority": "P3",
        "domain_id": None,
        "mayor_question": "Is civic footfall slipping?",
        "ask_prompt": "How are library visits trending as a secondary citizen signal?",
        "metrics": [("svc-libraries", "library_visits", "Library visits")],
        "blocker_if_empty": None,
        "ownership_note": "Secondary citizen-experience signal — never above Health, Safety, Housing, Water, or Energy.",
    },
]


def build_sectors_report(municipality: str = "CPT") -> SectorsReport:
    repo = get_repository()
    pulse = build_city_pulse(repo=repo)
    pulse_by_metric = {i.metric: i for i in pulse.items}
    series_keys = {(s.entity_id, s.metric) for s in repo.metric_series()}

    domains = {d["id"]: d for d in list_domains(municipality)}
    risks = assess_risks(repo.service_areas(), repo.metric_series(), repo.budget_lines())
    risks, _ = attach_valuations(risks, [], repo.metric_series(), municipality)
    risks = attach_affected(risks, municipality)

    sectors: list[CriticalSector] = []
    for defn in _SPINE:
        metric_refs = [
            SectorMetricRef(entity_id=e, metric=m, label=lab) for e, m, lab in defn.get("metrics", [])
        ]
        present = [mr for mr in metric_refs if (mr.entity_id, mr.metric) in series_keys]
        directions = []
        headlines = []
        for mr in present:
            item = pulse_by_metric.get(mr.metric)
            if item:
                directions.append(item.direction)
                headlines.append(f"{mr.label}: {item.latest} ({item.direction})")

        if not directions:
            status = "unknown"
        elif len(set(directions)) == 1:
            status = directions[0]
        else:
            status = "mixed"

        domain_id = defn.get("domain_id")
        domain = domains.get(domain_id) if domain_id else None
        domain_available = bool(domain and domain.get("available"))

        affected = domain_affected(municipality, domain_id) if domain_id else None
        if affected is None and present:
            from helm.demographics import lookup_affected

            affected = lookup_affected(municipality, metric=present[0].metric)

        # Best matching risk for this sector's metrics
        top_risk = None
        metric_names = {mr.metric for mr in present}
        for r in risks:
            if r.forecast and r.forecast.metric in metric_names:
                top_risk = r
                break
            if any(m in r.id for m in metric_names):
                top_risk = r
                break

        has_signal = bool(present) or domain_available
        blocker = None
        if not has_signal:
            blocker = defn.get("blocker_if_empty")
        elif status == "unknown" and domain_available and not present:
            blocker = defn.get("blocker_if_empty") or "Domain snapshot only — no monthly ops series yet."
        elif affected and affected.gaps:
            # Keep blocker light when we have signal but demographic gaps remain
            if not present and domain_available:
                blocker = affected.gaps[0]

        sectors.append(
            CriticalSector(
                id=defn["id"],
                name=defn["name"],
                priority=defn["priority"],
                domain_id=domain_id,
                href=f"/{municipality}/domains/{domain_id}" if domain_id and domain_available else "/#sectors",
                mayor_question=defn["mayor_question"],
                ownership_note=defn.get("ownership_note"),
                status=status,
                domain_available=domain_available,
                ops_series_count=len(present),
                has_affected=affected is not None and (
                    affected.population_estimate is not None or bool(affected.gaps)
                ),
                headline="; ".join(headlines) if headlines else (
                    domain.get("summary")[:120] + "…" if domain and domain.get("summary") else None
                ),
                blocker=blocker,
                ask_prompt=defn["ask_prompt"],
                metrics=metric_refs,
                affected=affected,
                top_risk_id=top_risk.id if top_risk else None,
                top_risk_title=top_risk.title if top_risk else None,
            )
        )

    p0 = [s for s in sectors if s.priority == "P0"]
    p0_ready = sum(1 for s in p0 if s.ops_series_count > 0 or (s.domain_available and s.status != "unknown"))

    return SectorsReport(
        municipality=municipality,
        sectors=sectors,
        p0_ready_count=p0_ready,
        p0_total=len(p0),
    )
