"""Tests for actions, valuation, value ledger, periods and snapshot honesty."""
from fastapi.testclient import TestClient

from helm.actions import build_action_register
from helm.api.main import app
from helm.core.cache import cache_clear
from helm.core.periods import format_month
from helm.pulse import build_city_pulse
from helm.snapshot import build_city_snapshot
from helm.valuation import attach_valuations, estimate_risk_cost, valuation_catalog
from helm.value_ledger import build_value_ledger
from helm.core.models import Forecast, Priority, Risk, Trend
from helm.persistence import get_repository

client = TestClient(app)


def test_format_month():
    assert format_month("2026-02-01") == "February 2026"
    assert format_month(None) is None


def test_pulse_has_explicit_periods():
    pulse = build_city_pulse()
    assert pulse.data_through == "February 2026"
    assert pulse.previous_period == "January 2026"
    assert "February 2026" in pulse.period_note
    assert "January 2026" in pulse.period_note
    assert pulse.cadence == "monthly"


def test_snapshot_has_no_duplicate_health_kpi():
    cache_clear()
    snap = build_city_snapshot("CPT")
    keys = [k.key for k in snap.kpis]
    assert "health" not in keys
    assert snap.health_score >= 0
    assert snap.data_through == "February 2026"
    assert snap.brief_refreshed_at


def test_action_register_flags_overdue():
    reg = build_action_register("CPT")
    assert reg.actions
    assert reg.overdue_count >= 1
    assert reg.actions[0].status == "overdue"
    assert any(a.department for a in reg.actions)
    assert any(a.due_date for a in reg.actions)


def test_actions_endpoint():
    res = client.get("/actions")
    assert res.status_code == 200
    body = res.json()
    assert body["open_count"] >= 1
    assert body["total_expected_impact_zar"] > 0


def test_valuation_catalog_has_assumptions():
    catalog = valuation_catalog("CPT")
    nrw = catalog["metrics"]["non_revenue_water_pct"]
    assert nrw["rand_per_unit_per_year"] > 0
    assert nrw["assumptions"]
    assert nrw["method"]


def test_risk_cost_estimate_attached():
    repo = get_repository()
    series = next(s for s in repo.metric_series() if s.metric == "non_revenue_water_pct")
    risk = Risk(
        id="risk-svc-water-non_revenue_water_pct",
        title="NRW",
        reason="test",
        likelihood=0.9,
        impact=0.9,
        trend=1.2,
        confidence=0.9,
        priority=Priority.CRITICAL,
        owner="test",
        mitigation="test",
        forecast=Forecast(
            entity_id="svc-water",
            metric="non_revenue_water_pct",
            direction=Trend.WORSENING,
            slope=0.8,
            projected_next=28,
            confidence=0.9,
        ),
    )
    est = estimate_risk_cost(risk, series, "CPT")
    assert est is not None
    assert est.amount_zar > 1_000_000_000  # ~27.8pp × R185m
    assert est.assumptions


def test_attach_valuations_on_brief_risks():
    cache_clear()
    brief = client.get("/brief").json()
    assert brief["top_risks"]
    with_cost = [r for r in brief["top_risks"] if r.get("cost_estimate")]
    assert with_cost, "at least one risk should carry a cost estimate"


def test_value_ledger_totals():
    ledger = build_value_ledger("CPT")
    assert ledger.entries
    assert ledger.cumulative_attributed_zar == (
        ledger.cumulative_projected_zar
        + ledger.cumulative_realised_zar
        + ledger.cumulative_avoided_zar
    )
    assert ledger.cumulative_attributed_zar > 0


def test_value_ledger_endpoint():
    res = client.get("/value-ledger")
    assert res.status_code == 200
    assert res.json()["cumulative_attributed_zar"] > 0


def test_feeds_have_last_refreshed_label():
    res = client.get("/feeds")
    assert res.status_code == 200
    for feed in res.json()["feeds"]:
        assert "last_refreshed_label" in feed
        assert feed["last_refreshed_label"]
