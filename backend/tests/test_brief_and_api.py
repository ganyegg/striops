from fastapi.testclient import TestClient

from helm.api.main import app
from helm.executive_brief import build_executive_brief

client = TestClient(app)


def test_brief_is_intelligence_first():
    brief = build_executive_brief()
    assert brief.greeting.startswith("Good")
    assert 0 <= brief.health_score <= 100
    assert brief.top_risks, "brief must surface risks"
    assert brief.top_opportunities, "brief must surface opportunities"
    assert brief.recommended_decisions, "brief must recommend actions"
    assert brief.strategic_summary
    # Every recommendation must be explainable + evidenced.
    for rec in brief.recommended_decisions:
        assert rec.rationale
        assert 0 <= rec.confidence <= 1


def test_agent_contributions_present():
    brief = build_executive_brief()
    names = {c.agent for c in brief.agent_contributions}
    assert "Risk Agent" in names
    assert "Finance Agent" in names


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] in ("mock", "gemini")


def test_brief_endpoint():
    r = client.get("/brief")
    assert r.status_code == 200
    assert r.json()["health_score"] >= 0


def test_simulate_endpoint():
    r = client.post("/simulate", json={"function_name": "Solid Waste Management", "pct_change": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["recommended"]
    assert body["scenario"]["impacts"]


def test_simulate_bad_function_returns_400():
    r = client.post("/simulate", json={"function_name": "Nope", "pct_change": 10})
    assert r.status_code == 400


def test_agents_roster():
    r = client.get("/agents")
    assert r.status_code == 200
    roles = {a["name"] for a in r.json()}
    assert "Executive Agent" in roles
    assert "Simulation Agent" in roles
