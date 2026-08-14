from fastapi.testclient import TestClient

from striops.api.main import app
from striops.wins import list_initiatives

client = TestClient(app)


def test_wins_seeded():
    wins = list_initiatives("CPT")
    assert len(wins) >= 5
    assert any("pipe" in w.id for w in wins)


def test_api_wins():
    r = client.get("/wins")
    assert r.status_code == 200
    assert r.json()[0]["plain_language"]


def test_stale_win_claim_is_flagged_against_its_own_metric():
    """The lighting win claims a falling trend the live C3 series no longer shows."""
    wins = list_initiatives("CPT")
    lighting = next(w for w in wins if w.id == "win-lighting-reliability")
    assert lighting.data_check in ("contradicted", "unverified")
    assert lighting.data_check_note


def test_flagged_wins_never_lead_the_page():
    wins = list_initiatives("CPT")
    flagged = [n for n, w in enumerate(wins) if w.data_check in ("contradicted", "unverified")]
    clean = [n for n, w in enumerate(wins) if w.data_check not in ("contradicted", "unverified")]
    if flagged and clean:
        assert min(flagged) > max(clean)


def test_wins_without_a_related_metric_are_left_alone():
    """Curated narrative that cites no series is not second-guessed."""
    wins = list_initiatives("CPT")
    for w in wins:
        if not w.related_metric:
            assert w.data_check is None


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
