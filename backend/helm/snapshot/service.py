"""Mayor-facing city snapshot — the numbers that should sit above the fold."""
from __future__ import annotations

from datetime import datetime

from helm.core.glossary import explain
from helm.core.models import CitySnapshot, HeroKPI
from helm.domains import get_domain
from helm.executive_brief import build_executive_brief
from helm.wins import list_initiatives


def _greeting(city: str) -> str:
    hour = datetime.now().hour
    part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    return f"Good {part}, {city}."


def build_city_snapshot(code: str = "CPT") -> CitySnapshot:
    brief = build_executive_brief()
    city = brief.generated_for
    wins = list_initiatives(code)

    # Pull verified budget / water headline figures from domain profiles.
    budget_total = "R87.79bn"
    infra = "R40bn"
    water_capex = "R16.7bn"
    safety = "R6.8bn"
    dams = "~78%"
    try:
        budget = get_domain(code, "budget")
        by_key = {i.key: i for i in budget.indicators}
        budget_total = by_key.get("total", budget.indicators[0]).value
        infra = by_key["infra_3yr"].value.split("(")[0].strip() if "infra_3yr" in by_key else infra
        water_capex = by_key["water_capital"].value if "water_capital" in by_key else water_capex
    except Exception:
        pass
    try:
        water = get_domain(code, "water")
        dam_ind = next((i for i in water.indicators if i.key == "dams"), None)
        if dam_ind:
            dams = dam_ind.value.split("(")[0].strip()
    except Exception:
        pass
    try:
        safety_d = get_domain(code, "safety_policing")
        sb = next((i for i in safety_d.indicators if i.key == "safety_budget"), None)
        if sb:
            safety = sb.value.split("(")[0].strip()
    except Exception:
        pass

    nrw = explain("non_revenue_water_pct")
    dam_g = explain("dam_storage")

    critical = sum(1 for r in brief.top_risks if r.priority.value in ("critical", "high"))

    kpis = [
        HeroKPI(
            key="health",
            label="Strategic health",
            value=f"{brief.health_score}",
            hint="/100",
            tone="warn" if brief.health_score < 70 else "good",
            href="/",
            plain_language="Composite of active risks vs redeployable opportunities.",
        ),
        HeroKPI(
            key="budget",
            label="Adopted budget",
            value=budget_total,
            hint="2026/27",
            tone="neutral",
            href=f"/{code}/domains/budget/indicators/total",
            plain_language="Total City of Hope budget adopted by Council.",
        ),
        HeroKPI(
            key="infra",
            label="3-yr infrastructure",
            value=infra,
            hint="MTREF",
            tone="good",
            href="/wins/win-city-of-hope-capex",
            plain_language="Protected basic infrastructure investment over three years.",
        ),
        HeroKPI(
            key="water",
            label="Water & sanitation capital",
            value=water_capex,
            hint="40% of capex",
            tone="good",
            href="/wins/win-pipe-replacement",
            plain_language="Largest capital share — pipes, wastewater, supply.",
        ),
        HeroKPI(
            key="dams",
            label="Dam storage",
            value=dams,
            hint="vs ~82% last year",
            tone="warn",
            href=f"/{code}/domains/water",
            plain_language=dam_g["in_one_line"] if dam_g else "How full the major dams are.",
        ),
        HeroKPI(
            key="safety",
            label="Safety budget",
            value=safety,
            hint="record",
            tone="good",
            href="/wins/win-safety-capacity",
            plain_language="Record safety & security allocation for 2026/27.",
        ),
        HeroKPI(
            key="risks",
            label="High / critical risks",
            value=str(critical),
            hint="active",
            tone="bad" if critical else "good",
            href="/#risks",
            plain_language="Risks ranked high or critical that need a decision this cycle.",
        ),
        HeroKPI(
            key="wins",
            label="Delivery wins tracked",
            value=str(len(wins)),
            hint="initiatives",
            tone="good",
            href="/#wins",
            plain_language="Verified or strongly sourced initiatives that are working.",
        ),
    ]

    return CitySnapshot(
        municipality=city,
        greeting=_greeting(city),
        tagline="Steer before the storm. Celebrate what is working.",
        health_score=brief.health_score,
        kpis=kpis,
        confidence_note=(
            "Figures marked Verified are cross-checked to City / Treasury / DWS public sources. "
            "Crime and staffing claims stay Needs verification until the exact SAPS quarter "
            "or Annual Report line is attached. Non-revenue water: "
            + (nrw["in_one_line"] if nrw else "unbilled water losses.")
        ),
    )
