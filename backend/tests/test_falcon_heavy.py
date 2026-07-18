"""Provenance, comparatives, ask, refresh, and health-sector coverage."""
from fastapi.testclient import TestClient

from striops.api.main import app
from striops.comparatives import build_comparatives
from striops.core.cache import cache_clear
from striops.core.models import Opportunity, Priority, Risk
from striops.health_score import build_health_breakdown, compute_health_breakdown

client = TestClient(app)


def test_health_breakdown_line_items():
    cache_clear()
    bd = build_health_breakdown("CPT")
    assert 0 <= bd.health_score <= 100
    assert bd.base == 100
    assert bd.risk_lines
    assert abs(bd.risk_penalty_raw - sum(line.contribution for line in bd.risk_lines)) < 0.02
    assert bd.formula_plain_language
    r = client.get("/health-breakdown")
    assert r.status_code == 200
    assert r.json()["health_score"] == bd.health_score


def test_health_breakdown_formula_caps():
    risks = [
        Risk(
            id=f"r{i}",
            title=f"Risk {i}",
            reason="x",
            likelihood=1.0,
            impact=1.0,
            trend=2.0,
            confidence=1.0,
            priority=Priority.CRITICAL,
            owner="x",
            mitigation="x",
        )
        for i in range(5)
    ]
    # score = 100 each → raw penalty 80 → capped 55
    opps = [
        Opportunity(
            id=f"o{i}",
            title=f"Opp {i}",
            reason="x",
            value_estimate=1_000_000,
            confidence=0.8,
            priority=Priority.MEDIUM,
            owner="x",
            action="x",
        )
        for i in range(5)
    ]
    bd = compute_health_breakdown(risks, opps)
    assert bd.risk_cap_applied
    assert bd.risk_penalty_capped == 55.0
    assert bd.opportunity_cap_applied
    assert bd.opportunity_bonus_capped == 8.0
    assert bd.health_score == 53  # 100 - 55 + 8


def test_comparatives_include_water_and_health():
    cache_clear()
    report = build_comparatives(municipality="CPT")
    ids = {p.id for p in report.packs}
    assert "water_stress" in ids
    assert "health_access" in ids
    water = next(p for p in report.packs if p.id == "water_stress")
    assert len(water.series) == 2
    assert water.ratio is not None
    r = client.get("/comparatives")
    assert r.status_code == 200
    assert len(r.json()["packs"]) >= 2


def test_ask_returns_grounded_answer():
    cache_clear()
    r = client.post("/ask", json={"question": "How is clinic access trending?", "mode": "answer"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"]
    assert body["citations"]
    assert body["used_facts"]
    r2 = client.post("/ask", json={"question": "Summarise strategic health", "mode": "report"})
    assert r2.status_code == 200
    assert r2.json()["report_markdown"]


def test_refresh_clears_and_reports():
    cache_clear()
    r = client.post("/refresh?run_ingest=false")
    assert r.status_code == 200
    body = r.json()
    assert body["brief_cache_cleared"] is True
    assert body["refreshed_at"]


def test_health_domain_available():
    r = client.get("/municipalities/CPT/domains")
    assert r.status_code == 200
    health = next(d for d in r.json() if d["id"] == "health")
    assert health["available"] is True
    assert health["indicator_count"] >= 2
    profile = client.get("/municipalities/CPT/domains/health")
    assert profile.status_code == 200
    assert profile.json()["id"] == "health"
