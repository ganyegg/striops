"""Critical sectors spine + demographics."""
from fastapi.testclient import TestClient

from helm.api.main import app
from helm.core.cache import cache_clear
from helm.demographics import attach_affected, clear_affected_cache
from helm.persistence import get_repository
from helm.pulse import build_city_pulse
from helm.risk_engine import assess_risks
from helm.sectors import build_sectors_report
from helm.valuation import attach_valuations

client = TestClient(app)


def test_sectors_report_orders_p0_and_demotes_libraries():
    cache_clear()
    clear_affected_cache()
    report = build_sectors_report("CPT")
    ids = [s.id for s in report.sectors]
    assert ids.index("health") < ids.index("libraries")
    assert ids.index("water") < ids.index("libraries")
    health = next(s for s in report.sectors if s.id == "health")
    assert health.ops_series_count >= 2
    assert health.affected is not None
    assert "hospital" in (health.ownership_note or "").lower() or "DoH" in (health.ownership_note or "")
    r = client.get("/sectors")
    assert r.status_code == 200
    assert r.json()["p0_total"] >= 5


def test_pulse_puts_health_before_libraries():
    cache_clear()
    pulse = build_city_pulse()
    metrics = [i.metric for i in pulse.items]
    if "clinic_waiting_days" in metrics and "library_visits" in metrics:
        assert metrics.index("clinic_waiting_days") < metrics.index("library_visits")


def test_risks_carry_affected():
    cache_clear()
    clear_affected_cache()
    repo = get_repository()
    risks = assess_risks(repo.service_areas(), repo.metric_series(), repo.budget_lines())
    risks, _ = attach_valuations(risks, [], repo.metric_series(), "CPT")
    risks = attach_affected(risks, "CPT")
    health_risks = [r for r in risks if "clinic" in r.id or "ems" in r.id]
    assert health_risks
    assert any(r.affected and r.affected.population_estimate for r in health_risks)


def test_ask_hospital_gap_protocol():
    cache_clear()
    clear_affected_cache()
    r = client.post(
        "/ask",
        json={"question": "What is hospital occupancy in Cape Town?", "mode": "answer"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "hospital" in body["answer"].lower() or "DoH" in body["answer"] or "provincial" in body["answer"].lower()
    assert body.get("data_gaps") is not None


def test_normalize_smashed_ask_markdown():
    from helm.ask.service import normalize_answer_markdown

    smashed = (
        "### Snapshot Khayelitsha, with an estimated 400,000 residents, is a focus. "
        "### Evidence * **Transport**: MyCiTi funded in 2026/27 MTREF. "
        "* **Safety**: R6.8bn in 2026/27. "
        "### Watch (metro-wide through February 2026) * **Water**: Dam storage worsening. "
        "### Gaps * No Khayelitsha-only clinic series."
    )
    fixed = normalize_answer_markdown(smashed)
    assert "### Snapshot\n" in fixed
    assert "\n- **Transport**" in fixed or "\n- **Transport**:" in fixed
    assert fixed.count("\n### ") >= 3
    assert "### Snapshot Khayelitsha" not in fixed


def test_ask_khayelitsha_place_dossier():
    cache_clear()
    from helm.places import clear_places_cache, detect_places

    clear_places_cache()
    assert detect_places("Khayelitsha")
    r = client.post("/ask", json={"question": "Khayelitsha", "mode": "answer"})
    assert r.status_code == 200
    body = r.json()
    answer = body["answer"].lower()
    assert "khayelitsha" in answer
    assert "no information" not in answer and "does not contain specific information" not in answer
    assert "myciti" in answer or "transport" in answer or "cape flats" in answer
    assert any("khayelitsha" in (g.get("sector_name") or "").lower() for g in body.get("data_gaps") or [])
    # Readable structure after normalize
    assert "### snapshot" in answer
    assert "\n- " in body["answer"] or "\n*" in body["answer"]


def test_waste_and_transport_domains_live():
    cache_clear()
    domains = client.get("/municipalities/CPT/domains").json()
    by_id = {d["id"]: d for d in domains}
    assert by_id["waste"]["available"] is True
    assert by_id["transport"]["available"] is True
