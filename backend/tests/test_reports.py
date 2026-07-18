from fastapi.testclient import TestClient

from striops.api.main import app
from striops.reports import build_metric_report, build_risk_report

client = TestClient(app)


def test_build_metric_report_has_series_and_refs():
    report = build_metric_report("svc-water", "non_revenue_water_pct")
    assert report.series
    assert report.projected
    assert report.stats.n_points >= 2
    assert report.references
    assert all(r.url.startswith("http") for r in report.references)


def test_build_risk_report_embeds_metric():
    report = build_risk_report("risk-svc-water-non_revenue_water_pct")
    assert report.risk.score > 0
    assert report.score_breakdown.score == report.risk.score
    assert report.metric_report is not None
    assert report.metric_report.series
    assert report.references


def test_api_risk_report():
    r = client.get("/risks/risk-svc-water-non_revenue_water_pct")
    assert r.status_code == 200
    body = r.json()
    assert body["metric_report"]["series"]
    assert body["references"]


def test_api_metric_report():
    r = client.get("/metrics/svc-roads/road_maintenance_backlog_km")
    assert r.status_code == 200
    assert r.json()["stats"]["n_points"] >= 2


def test_api_indicator_report():
    r = client.get("/municipalities/CPT/domains/budget/indicators/total")
    assert r.status_code == 200
    body = r.json()
    assert body["indicator"]["value"] == "R87.79bn"
    assert body["references"]


def test_api_unknown_risk_404():
    assert client.get("/risks/risk-does-not-exist").status_code == 404
