"""City Themes — mayoral spine mapped to evidence."""

from striops.themes import build_themes_report


def test_themes_cover_mayoral_spine():
    report = build_themes_report("CPT")
    ids = {t.id for t in report.themes}
    assert {
        "water",
        "energy",
        "safety",
        "housing",
        "fiscal",
        "infrastructure",
        "waste",
        "mobility",
    } <= ids
    assert report.live_theme_count >= 1
    assert "FY2025/26" in report.official_anchor or "2025/26" in report.official_anchor
    assert "financial_year" in report.fiscal_period_note
    assert report.value_over_reports
    assert all(t.mayor_question and t.striops_adds for t in report.themes)


def test_themes_api(client=None):
    from fastapi.testclient import TestClient

    from striops.api.main import app

    c = client or TestClient(app)
    res = c.get("/themes")
    assert res.status_code == 200
    body = res.json()
    assert len(body["themes"]) >= 6
    assert "fiscal_period_note" in body
