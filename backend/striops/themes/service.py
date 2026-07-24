"""City Themes — close the gap between Mayoral priorities and Striops evidence.

Maps the City of Hope / Mayoral Minute / S52 agenda onto live Open Data, domain
profiles, and explicit gaps — so executives see *their* themes first, with what
a continuous OS adds over a quarterly PDF.
"""
from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from striops.core.config import Settings, get_settings
from striops.domains import get_domain
from striops.persistence import get_repository
from striops.pulse import build_city_pulse


class ThemeEvidence(BaseModel):
    label: str
    value: str
    period: str | None = None
    provenance: str = "demonstration"  # live | demonstration | official | gap
    href: str | None = None


class CityTheme(BaseModel):
    id: str
    name: str
    mayor_question: str
    city_says: str  # what recent reports emphasise
    striops_adds: str  # continuous value vs PDF
    status: str  # watching | improving | worsening | mixed | gap
    readiness: str  # live | partial | awaiting_extract
    evidence: list[ThemeEvidence] = Field(default_factory=list)
    gap: str | None = None
    ask_prompt: str


class ValueDifferentiator(BaseModel):
    title: str
    report_does: str
    striops_does: str


class ThemesReport(BaseModel):
    municipality: str
    generated_at: str
    source_note: str
    fiscal_period_note: str
    official_anchor: str
    themes: list[CityTheme]
    value_over_reports: list[ValueDifferentiator]
    live_theme_count: int
    gap_theme_count: int


def _pulse_lookup(pulse) -> dict[str, object]:
    return {i.metric: i for i in pulse.items}


def _ev_from_pulse(item, href: str | None = None) -> ThemeEvidence:
    return ThemeEvidence(
        label=item.label,
        value=f"{item.latest:,.2f}".rstrip("0").rstrip(".") + (f" {item.unit}" if item.unit else ""),
        period=item.latest_period,
        provenance=item.provenance or "demonstration",
        href=href or item.href,
    )


def _domain_value(code: str, domain_id: str, key: str) -> tuple[str | None, str]:
    try:
        profile = get_domain(code, domain_id)
        ind = next((i for i in profile.indicators if i.key == key), None)
        if not ind:
            return None, "gap"
        prov = getattr(ind.verification, "value", None) or str(ind.verification)
        if prov == "verified":
            return ind.value, "official"
        if prov == "needs_verification":
            return ind.value, "demonstration"
        return ind.value, "demonstration"
    except Exception:
        return None, "gap"


def build_themes_report(
    code: str = "CPT",
    settings: Settings | None = None,
) -> ThemesReport:
    settings = settings or get_settings()
    pulse = build_city_pulse(settings=settings)
    by_metric = _pulse_lookup(pulse)
    repo = get_repository(settings)

    # Latest seed fiscal year (full-year budget vs actual — not mid-year YTD).
    fy_years = sorted({b.financial_year for b in repo.budget_lines()})
    latest_fy = fy_years[-1] if fy_years else None
    fiscal_period_note = (
        f"Fiscal chart / underspend opportunities use demonstration full-year function totals "
        f"labelled financial_year={latest_fy} (treated as closed-year budget vs actual). "
        f"They are NOT the City’s official mid-year YTD for municipal FY2025/26 "
        f"(1 Jul 2025 – 30 Jun 2026). Official in-year anchor: Mayor’s S52 report to "
        f"31 December 2025 (Q2)."
        if latest_fy
        else "No budget lines loaded."
    )

    themes: list[CityTheme] = []

    # ── 1. Water security ──────────────────────────────────────────────
    water_ev: list[ThemeEvidence] = []
    water_status = "gap"
    if "dam_storage" in by_metric:
        water_ev.append(_ev_from_pulse(by_metric["dam_storage"]))
        water_status = by_metric["dam_storage"].direction
    if "dws_system_storage" in by_metric:
        water_ev.append(_ev_from_pulse(by_metric["dws_system_storage"]))
        if water_status == "gap":
            water_status = by_metric["dws_system_storage"].direction
    if "non_revenue_water_pct" in by_metric:
        water_ev.append(_ev_from_pulse(by_metric["non_revenue_water_pct"]))
        if water_status == "gap":
            water_status = by_metric["non_revenue_water_pct"].direction
        elif water_status != by_metric["non_revenue_water_pct"].direction:
            water_status = "mixed"
    nrw_val, _ = _domain_value(code, "water", "nrw")
    themes.append(
        CityTheme(
            id="water",
            name="Water & sanitation security",
            mayor_question="Are we losing water while bulk storage still cushions us — and what do we decide this month?",
            city_says=(
                "City of Hope / adjustments budgets put Water & Sanitation at the centre of "
                "capital (largest capex share); S52 tracks WWTW and bulk projects mid-year."
            ),
            striops_adds=(
                "Watches measured dam storage and loss signals continuously; prices the "
                "loss–storage gap; refuses to invent NRW when the departmental extract is missing."
            ),
            status=water_status if water_ev else "gap",
            readiness=(
                "live"
                if "dam_storage" in by_metric or "dws_system_storage" in by_metric
                else "awaiting_extract"
            ),
            evidence=water_ev,
            gap=(
                None
                if "non_revenue_water_pct" in by_metric
                and by_metric["non_revenue_water_pct"].provenance == "live"
                else "Live NRW + project-level WWTW spend need Water departmental extract (MOU)."
            ),
            ask_prompt="Where is water risk concentrated and what should we decide this month?",
        )
    )

    # ── 2. Energy security ─────────────────────────────────────────────
    energy_ev: list[ThemeEvidence] = []
    for m in ("system_energy_kwh", "electricity_billed_kwh", "public_lighting_outages"):
        if m in by_metric:
            energy_ev.append(_ev_from_pulse(by_metric[m]))
    energy_dirs = [
        by_metric[m].direction for m in ("system_energy_kwh", "public_lighting_outages") if m in by_metric
    ]
    energy_status = "watching"
    if energy_dirs:
        if all(d == "worsening" for d in energy_dirs):
            energy_status = "worsening"
        elif all(d == "improving" for d in energy_dirs):
            energy_status = "improving"
        elif len(set(energy_dirs)) > 1:
            energy_status = "mixed"
        else:
            energy_status = energy_dirs[0]
    themes.append(
        CityTheme(
            id="energy",
            name="Energy security & grid load",
            mayor_question="Is the City’s energy system carrying peak load — and where are streetlight faults rising?",
            city_says=(
                "Mayoral Minute 2025 highlights own-generation (e.g. landfill gas-to-power) "
                "and grid investment while national supply remains unstable."
            ),
            striops_adds=(
                "Live monthly system energy and billed kWh from Open Data; live streetlight "
                "fault counts from C3 — a citizen-facing energy reliability signal reports don’t refresh daily."
            ),
            status=energy_status if energy_ev else "gap",
            readiness="live" if energy_ev else "awaiting_extract",
            evidence=energy_ev,
            gap="Own-generation MWh and Steenbras/IPP plant KPIs not yet wired — add Energy extract.",
            ask_prompt="How is system energy and public lighting trending — what should Energy watch?",
        )
    )

    # ── 3. Safety ──────────────────────────────────────────────────────
    safety_budget, safety_prov = _domain_value(code, "safety_policing", "safety_budget")
    leap, leap_prov = _domain_value(code, "safety_policing", "leap")
    safety_ev: list[ThemeEvidence] = []
    safety_status = "gap"
    if "murder_count" in by_metric:
        safety_ev.append(_ev_from_pulse(by_metric["murder_count"]))
        safety_status = by_metric["murder_count"].direction
    if "contact_crime_count" in by_metric:
        safety_ev.append(_ev_from_pulse(by_metric["contact_crime_count"]))
        if safety_status == "gap":
            safety_status = by_metric["contact_crime_count"].direction
    if safety_budget:
        safety_ev.append(
            ThemeEvidence(
                label="Safety budget (domain)",
                value=safety_budget.split("(")[0].strip(),
                provenance=safety_prov,
                href=f"/{code}/domains/safety_policing",
            )
        )
    if leap:
        safety_ev.append(
            ThemeEvidence(
                label="LEAP / safety capacity",
                value=leap.split("(")[0].strip()[:80],
                provenance=leap_prov,
                href=f"/{code}/domains/safety_policing",
            )
        )
    themes.append(
        CityTheme(
            id="safety",
            name="Safety & policing capacity",
            mayor_question="Is safety capacity expanding where residents feel it — and what’s still a data gap?",
            city_says=(
                "Mayoral Minute 2025 cites the largest Metro Police expansion in years and "
                "continued push on gang/gun violence and LEAP partnership."
            ),
            striops_adds=(
                "Rolls SAPS station stats up to the metro monthly (murder + contact crime) "
                "with Live badges; still flags Metro Police deployment as a gap."
            ),
            status=safety_status if safety_ev else "gap",
            readiness="live" if "murder_count" in by_metric else "partial",
            evidence=safety_ev,
            gap="Metro Police / LEAP deployment counts (monthly) still need a City extract.",
            ask_prompt="What do we know on safety & policing — and what is still missing?",
        )
    )

    # ── 4. Housing ─────────────────────────────────────────────────────
    pop_val, pop_prov = _domain_value(code, "housing_population", "population")
    backlog, b_prov = _domain_value(code, "housing_population", "housing_backlog")
    delivery, d_prov = _domain_value(code, "housing_population", "delivery_lag")
    housing_ev: list[ThemeEvidence] = []
    if "population" in by_metric:
        housing_ev.append(_ev_from_pulse(by_metric["population"]))
    elif pop_val:
        housing_ev.append(
            ThemeEvidence(
                label="Population (Census)",
                value=pop_val,
                provenance=pop_prov,
                href=f"/{code}/domains/housing_population",
            )
        )
    for label, val, prov in (
        ("Housing backlog", backlog, b_prov),
        ("Delivery lag", delivery, d_prov),
    ):
        if val:
            housing_ev.append(
                ThemeEvidence(
                    label=label,
                    value=val.split("(")[0].strip()[:90],
                    provenance=prov,
                    href=f"/{code}/domains/housing_population",
                )
            )
    themes.append(
        CityTheme(
            id="housing",
            name="Housing & human settlements",
            mayor_question="Is housing delivery keeping pace with the backlog — monthly, not annually?",
            city_says=(
                "Mayoral Minute and budget speeches frame housing/planning reform and "
                "human settlements grants (USDG/ISUPG) as central to City of Hope."
            ),
            striops_adds=(
                "Surfaces the theme as a mayoral question with an explicit data request — "
                "empty is a blocker, not silence."
            ),
            status="watching" if housing_ev else "gap",
            readiness="partial" if pop_val or "population" in by_metric else "awaiting_extract",
            evidence=housing_ev,
            gap="Needs monthly units delivered vs target from Human Settlements (aggregate extract).",
            ask_prompt="Housing backlog and delivery — what is known and what is missing?",
        )
    )

    # ── 5. Fiscal / revenue ────────────────────────────────────────────
    fiscal_ev: list[ThemeEvidence] = []
    if "municipal_arrears_zar" in by_metric:
        fiscal_ev.append(_ev_from_pulse(by_metric["municipal_arrears_zar"]))
    audit_val, audit_prov = _domain_value(code, "fiscal", "audit")
    if audit_val:
        fiscal_ev.append(
            ThemeEvidence(
                label="Audit outcome (AGSA)",
                value=audit_val[:80],
                provenance=audit_prov,
                href=f"/{code}/domains/fiscal",
            )
        )
    cash, cash_prov = _domain_value(code, "fiscal", "collection")
    if cash:
        fiscal_ev.append(
            ThemeEvidence(
                label="Collection (domain)",
                value=cash.split("(")[0].strip()[:80],
                provenance=cash_prov,
                href=f"/{code}/domains/fiscal",
            )
        )
    fiscal_status = (
        by_metric["municipal_arrears_zar"].direction if "municipal_arrears_zar" in by_metric else "watching"
    )
    themes.append(
        CityTheme(
            id="fiscal",
            name="Fiscal health & revenue",
            mayor_question="Are arrears and collection pressure rising while capital asks grow?",
            city_says=(
                "S52 to 31 Dec 2025 reports collection ratios (~98% band) and debtors; "
                "January 2026 adjustments budget reprioritises mid-year."
            ),
            striops_adds=(
                "Live municipal arrears stock from Open Data as a fiscal-distress signal; "
                "underspend opportunities are labelled as demonstration full-year until Finance extract is live."
            ),
            status=fiscal_status,
            readiness="partial",
            evidence=fiscal_ev,
            gap=(
                "Wire S52 YTD operating/capital tables and SAP Finance aggregates so "
                "underspend is official mid-year FY2025/26, not seed FY totals."
            ),
            ask_prompt="What is the fiscal pressure signal from arrears and where should we redeploy?",
        )
    )

    # ── 6. Infrastructure / capital delivery ───────────────────────────
    infra, infra_prov = _domain_value(code, "budget", "infra_3yr")
    water_capex, wc_prov = _domain_value(code, "budget", "water_capital")
    infra_ev: list[ThemeEvidence] = []
    if infra:
        infra_ev.append(
            ThemeEvidence(
                label="3-yr infrastructure",
                value=infra.split("(")[0].strip(),
                provenance=infra_prov,
                href="/#wins",
            )
        )
    if water_capex:
        infra_ev.append(
            ThemeEvidence(
                label="Water & sanitation capital",
                value=water_capex.split("(")[0].strip(),
                provenance=wc_prov,
                href="/wins/win-pipe-replacement",
            )
        )
    themes.append(
        CityTheme(
            id="infrastructure",
            name="Infrastructure & capital delivery",
            mayor_question="Is the capital programme on the mid-year plan — project by project?",
            city_says=(
                "Mayoral Minute cites ~R9–10bn infrastructure investment; S52 Q2 shows capital "
                "YTD vs YTD budget (~94.5% of mid-year plan to 31 Dec 2025)."
            ),
            striops_adds=(
                "Links capital themes to operational outcomes (water losses, lighting, refuse) "
                "so underspend debates are tied to service pressure — not a table alone."
            ),
            status="watching",
            readiness="partial",
            evidence=infra_ev,
            gap="Project-level capital YTD (vote/project) from Finance/S52 feed not yet ingested.",
            ask_prompt="How should we connect capital underspend to service pressure this cycle?",
        )
    )

    # ── 7. Waste & public realm ────────────────────────────────────────
    waste_ev: list[ThemeEvidence] = []
    waste_status = "gap"
    if "refuse_service_requests" in by_metric:
        waste_ev.append(_ev_from_pulse(by_metric["refuse_service_requests"]))
        waste_status = by_metric["refuse_service_requests"].direction
    themes.append(
        CityTheme(
            id="waste",
            name="Waste & public realm",
            mayor_question="Are refuse and dumping pressures rising where residents report them?",
            city_says="Service delivery and urban management remain standing City priorities in IDP/SDBIP framing.",
            striops_adds=(
                "Live monthly C3-derived refuse/dumping request volumes — a citizen pressure "
                "gauge that updates with Open Data, not only at quarter-end."
            ),
            status=waste_status,
            readiness="live" if waste_ev else "awaiting_extract",
            evidence=waste_ev,
            gap=None,
            ask_prompt="How are refuse service requests trending and what should Solid Waste do?",
        )
    )

    # ── 8. Mobility / roads ────────────────────────────────────────────
    roads_ev: list[ThemeEvidence] = []
    roads_status = "gap"
    if "road_maintenance_backlog_km" in by_metric:
        roads_ev.append(_ev_from_pulse(by_metric["road_maintenance_backlog_km"]))
        roads_status = by_metric["road_maintenance_backlog_km"].direction
    themes.append(
        CityTheme(
            id="mobility",
            name="Roads & mobility",
            mayor_question="Is the road backlog compounding faster than the capital run-rate?",
            city_says="Budget speeches protect roads & stormwater capital alongside IRT/MyCiTi programmes.",
            striops_adds="Tracks backlog trend against budget utilisation when extracts exist; flags demonstration series honestly.",
            status=roads_status,
            readiness="awaiting_extract",
            evidence=roads_ev,
            gap="Live road-condition / backlog extract from Urban Mobility not yet wired.",
            ask_prompt="Road maintenance backlog — trend, cost, and what to decide?",
        )
    )

    value_over = [
        ValueDifferentiator(
            title="Cadence",
            report_does="S52 / adjustments / Mayoral Minute — quarterly or annual narrative.",
            striops_does="Daily brief + live Open Data pulse; Refresh pulls on demand.",
        ),
        ValueDifferentiator(
            title="Decision link",
            report_does="Tables and explanations; action ownership lives elsewhere.",
            striops_does="Risk → recommendation → action register → value ledger in one spine.",
        ),
        ValueDifferentiator(
            title="Honesty under incomplete data",
            report_does="Often silent or delayed when a feed is late.",
            striops_does="Labels Live vs Demo; states gaps; never invents ward/hospital numbers.",
        ),
        ValueDifferentiator(
            title="Foresight",
            report_does="Describes the period just closed.",
            striops_does="Trends, simulations, and (roadmap) cost-of-delay on open decisions.",
        ),
        ValueDifferentiator(
            title="Memory",
            report_does="PDF archives; institutional amnesia on turnover.",
            striops_does="Decision log and provenance survive staff and administration changes.",
        ),
    ]

    live_n = sum(1 for t in themes if t.readiness == "live")
    gap_n = sum(1 for t in themes if t.readiness == "awaiting_extract" or t.status == "gap")

    return ThemesReport(
        municipality=code,
        generated_at=datetime.now(UTC).isoformat(),
        source_note=(
            "Themes synthesised from Mayoral Minute 2025, S52 to 31 Dec 2025, "
            "2025/26 Adjustments Budget (Jan 2026), and City of Hope budget framing — "
            "mapped to Striops live feeds and domain profiles."
        ),
        fiscal_period_note=fiscal_period_note,
        official_anchor="Municipal FY2025/26 (1 Jul 2025 – 30 Jun 2026); S52 mid-year to 31 Dec 2025.",
        themes=themes,
        value_over_reports=value_over,
        live_theme_count=live_n,
        gap_theme_count=gap_n,
    )
