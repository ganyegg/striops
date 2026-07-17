from fastapi.testclient import TestClient

from helm.api.main import app
from helm.wins import list_initiatives

client = TestClient(app)


def test_wins_seeded():
    wins = list_initiatives("CPT")
    assert len(wins) >= 5
    assert any("pipe" in w.id for w in wins)


def test_api_wins():
    r = client.get("/wins")
    assert r.status_code == 200
    assert r.json()[0]["plain_language"]


def test_api_win_report():
    r = client.get("/wins/win-pipe-replacement")
    assert r.status_code == 200
    body = r.json()
    assert body["references"]
    assert "401" in body["initiative"]["headline"]


def test_snapshot_has_kpis():
    r = client.get("/snapshot")
    assert r.status_code == 200
    body = r.json()
    assert body["kpis"]
    assert body["greeting"]


def test_glossary_nrw():
    r = client.get("/glossary/non_revenue_water_pct")
    assert r.status_code == 200
    assert "leak" in r.json()["definition"].lower()
