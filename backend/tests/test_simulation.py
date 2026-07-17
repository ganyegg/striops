import pytest

from helm.reasoning import MockProvider
from helm.simulation import list_scenarios, simulate


def test_scenarios_listed(repo):
    scenarios = list_scenarios(repo)
    assert scenarios
    assert any(s["function_name"] == "Solid Waste Management" for s in scenarios)


def test_increase_budget_improves_outcome(repo):
    res = simulate("Solid Waste Management", 10, repo=repo, llm=MockProvider())
    op = next(i for i in res.scenario.impacts if i.dimension == "operational")
    # More budget -> refuse complaints fall (negative delta).
    assert op.delta.startswith("-")
    assert res.recommended == "Proceed"
    assert res.baseline.impacts and res.scenario.impacts
    assert res.evidence


def test_decrease_budget_flags_risk(repo):
    res = simulate("Water and Sanitation", -15, repo=repo, llm=MockProvider())
    risk = next(i for i in res.scenario.impacts if i.dimension == "risk")
    assert risk.delta == "higher"
    assert "not proceed" in res.recommended.lower()


def test_unknown_function_raises(repo):
    with pytest.raises(ValueError):
        simulate("Nonexistent Function", 5, repo=repo, llm=MockProvider())
