"""Scenario simulation over budget decisions.

v0.1 ships one generic, well-instrumented scenario type: adjusting a budget
function by a percentage. The engine is structured so new scenario types (build
an asset, delay maintenance, change staffing) slot in behind the same contract.
"""
from __future__ import annotations

from striops.core.models import (
    BudgetLine,
    Evidence,
    Scenario,
    ScenarioImpact,
    SimulationResult,
)
from striops.persistence import Repository, get_repository
from striops.reasoning import LLMProvider, get_llm

# How responsive each function's headline outcome is to funding, and the
# operational metric it moves. Elasticities are deliberately conservative and
# explainable (documented assumptions, not black-box).
_FUNCTION_MODEL: dict[str, dict] = {
    "Solid Waste Management": {
        "metric": "refuse service requests",
        "elasticity": 0.6,  # 10% more budget -> ~6% fewer complaints
        "citizen": "Fewer missed collections and faster complaint resolution.",
        "environmental": "Less illegal dumping and cleaner public spaces.",
        "political": "Visible cleanliness improvements are high-salience with residents.",
    },
    "Water and Sanitation": {
        "metric": "non-revenue water losses",
        "elasticity": 0.5,
        "citizen": "More reliable supply and fewer outages.",
        "environmental": "Reduced water waste strengthens drought resilience.",
        "political": "Water security is politically critical in Cape Town.",
    },
    "Roads and Transport": {
        "metric": "road maintenance backlog",
        "elasticity": 0.45,
        "citizen": "Smoother roads and shorter commutes.",
        "environmental": "Better roads cut vehicle emissions from congestion.",
        "political": "Potholes are a top visible grievance.",
    },
    "Electricity": {
        "metric": "public lighting outages",
        "elasticity": 0.4,
        "citizen": "Improved safety and reliability of public lighting.",
        "environmental": "Efficiency upgrades reduce grid losses.",
        "political": "Reliability during load-shedding is highly visible.",
    },
    "Community and Libraries": {
        "metric": "library visits",
        "elasticity": 0.35,
        "citizen": "Expanded programming and access.",
        "environmental": "Negligible.",
        "political": "Community upliftment signal.",
    },
}


def list_scenarios(repo: Repository | None = None) -> list[dict]:
    repo = repo or get_repository()
    latest: dict[str, BudgetLine] = {}
    for line in sorted(repo.budget_lines(), key=lambda b: b.financial_year):
        latest[line.function_name] = line
    return [
        {
            "function_name": fn,
            "current_budget": bl.budget,
            "current_actual": bl.actual,
            "modelled": fn in _FUNCTION_MODEL,
        }
        for fn, bl in latest.items()
    ]


def _latest_line(repo: Repository, function_name: str) -> BudgetLine | None:
    lines = [b for b in repo.budget_lines() if b.function_name == function_name]
    return max(lines, key=lambda b: b.financial_year) if lines else None


def simulate(
    function_name: str,
    pct_change: float,
    repo: Repository | None = None,
    llm: LLMProvider | None = None,
) -> SimulationResult:
    """Simulate adjusting `function_name` budget by `pct_change` percent."""
    repo = repo or get_repository()
    llm = llm or get_llm()

    line = _latest_line(repo, function_name)
    if line is None:
        raise ValueError(f"Unknown budget function: {function_name}")

    model = _FUNCTION_MODEL.get(
        function_name,
        {"metric": "service outcomes", "elasticity": 0.3, "citizen": "Marginal service change.",
         "environmental": "Negligible.", "political": "Low visibility."},
    )
    elasticity = model["elasticity"]
    delta_budget = line.budget * (pct_change / 100.0)
    new_budget = line.budget + delta_budget
    outcome_change_pct = -(pct_change * elasticity)  # more budget -> outcome metric falls (improves)

    question = f"What happens if we change the {function_name} budget by {pct_change:+.0f}%?"

    baseline = Scenario(
        name="Baseline (no change)",
        description=f"{function_name} stays at R{line.budget / 1e9:.2f}bn.",
        impacts=[
            ScenarioImpact(dimension="financial", delta="R0", detail="No budget change.", confidence=0.95),
            ScenarioImpact(
                dimension="operational",
                delta="0%",
                detail=f"{model['metric'].title()} continues on its current trajectory.",
                confidence=0.75,
            ),
        ],
    )

    direction_word = "improve" if outcome_change_pct < 0 else "worsen"
    confidence = round(max(0.4, 0.85 - abs(pct_change) / 200), 3)

    scenario = Scenario(
        name=f"{function_name} {pct_change:+.0f}%",
        description=f"{function_name} moves to R{new_budget / 1e9:.2f}bn ({pct_change:+.0f}%).",
        impacts=[
            ScenarioImpact(
                dimension="financial",
                delta=f"R{delta_budget / 1e9:+.2f}bn",
                detail=(
                    f"Budget {'increases' if delta_budget > 0 else 'decreases'} by "
                    f"R{abs(delta_budget) / 1e9:.2f}bn per year."
                ),
                confidence=0.95,
            ),
            ScenarioImpact(
                dimension="operational",
                delta=f"{outcome_change_pct:+.1f}%",
                detail=(
                    f"{model['metric'].title()} projected to {direction_word} by "
                    f"~{abs(outcome_change_pct):.1f}% (elasticity {elasticity})."
                ),
                confidence=confidence,
            ),
            ScenarioImpact(
                dimension="citizen",
                delta=direction_word,
                detail=model["citizen"] if delta_budget > 0 else f"Risk of degraded service: {model['citizen'].lower()}",
                confidence=round(confidence - 0.05, 3),
            ),
            ScenarioImpact(
                dimension="environmental", delta="qualitative", detail=model["environmental"], confidence=0.55
            ),
            ScenarioImpact(
                dimension="political", delta="qualitative", detail=model["political"], confidence=0.5
            ),
            ScenarioImpact(
                dimension="risk",
                delta="lower" if delta_budget > 0 else "higher",
                detail=(
                    "Reduces the associated strategic risk trajectory."
                    if delta_budget > 0
                    else "Elevates the associated strategic risk; monitor closely."
                ),
                confidence=confidence,
            ),
        ],
    )

    recommended = "Proceed" if (delta_budget > 0 and abs(pct_change) <= 15) else (
        "Proceed with caution" if delta_budget > 0 else "Do not proceed without mitigation"
    )
    detail_fallback = (
        f"A {pct_change:+.0f}% change to {function_name} is projected to {direction_word} "
        f"{model['metric']} by ~{abs(outcome_change_pct):.1f}% at a fiscal cost of "
        f"R{abs(delta_budget) / 1e9:.2f}bn. {'Recommended given rising demand.' if delta_budget > 0 else 'Weigh against service-risk exposure.'}"
    )
    prompt = (
        f"Advise city leadership on this decision in 3 sentences. Decision: {question}. "
        f"Modelled operational effect: {outcome_change_pct:+.1f}% change in {model['metric']}. "
        f"Fiscal effect: R{delta_budget / 1e9:+.2f}bn. Be balanced and decisive."
    )
    try:
        detail = llm.generate(prompt, system="You are the Simulation Agent of Striops.") or detail_fallback
    except Exception:
        detail = detail_fallback

    alternatives = [
        "Fund the change from underspend in another function (fiscally neutral).",
        f"Phase the {pct_change:+.0f}% over two budget cycles to de-risk delivery.",
        "Pair the budget change with a delivery-performance target and monthly review.",
    ]

    return SimulationResult(
        question=question,
        baseline=baseline,
        scenario=scenario,
        recommended=recommended,
        recommendation_detail=detail,
        confidence=confidence,
        evidence=[
            Evidence(label="Current budget", value=f"R{line.budget / 1e9:.2f}bn", source="treasury"),
            Evidence(label="Current actual", value=f"R{line.actual / 1e9:.2f}bn", source="treasury"),
            Evidence(label="Elasticity assumption", value=str(elasticity), source="simulation model"),
        ],
        alternatives=alternatives,
    )
