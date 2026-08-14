"""Tests for the Pulse engine, feed transparency and decision register."""
from fastapi.testclient import TestClient

from striops.api.main import app
from striops.core.cache import cache_clear, cache_get, cache_set
from striops.decisions import build_decision_register
from striops.feeds import build_feeds_report
from striops.pulse import build_city_pulse

client = TestClient(app)


def test_pulse_has_direction_per_metric():
    pulse = build_city_pulse()
    assert pulse.items, "seed metrics should yield pulse items"
    for item in pulse.items:
        assert item.direction in ("improving", "worsening", "flat", "unverified")
        assert item.href.startswith("/metrics/")
        if item.needs_verification:
            # An unverified item states the break-out ratio instead of claiming
            # a percentage change it cannot defend.
            assert item.direction == "unverified"
            assert item.verification_note
            assert "verify" in item.sentence.lower()
        else:
            assert "%" in item.sentence


def test_pulse_flags_extract_artefacts_instead_of_claiming_a_change():
    """Refuse and lighting both break range in Jun 2026 — neither may lead the brief."""
    pulse = build_city_pulse()
    flagged = {i.metric for i in pulse.items if i.needs_verification}
    assert "refuse_service_requests" in flagged
    assert "public_lighting_outages" in flagged
    assert pulse.unverified_count == len(flagged)
    # Unverified rows are excluded from the headline counts.
    for item in pulse.items:
        if item.needs_verification:
            assert item.direction not in ("worsening", "improving")
    # ...and they sort below the live metrics that can defend themselves.
    live = [i for i in pulse.items if i.provenance == "live"]
    first_flagged = next(n for n, i in enumerate(live) if i.needs_verification)
    assert all(not i.needs_verification for i in live[:first_flagged])


def test_pulse_polarity_library_visits_up_is_improving():
    pulse = build_city_pulse()
    libs = next((i for i in pulse.items if i.metric == "library_visits"), None)
    if libs and libs.change > 0:
        assert libs.direction == "improving"


def test_pulse_endpoint():
    res = client.get("/pulse")
    assert res.status_code == 200
    body = res.json()
    assert body["worsening_count"] + body["improving_count"] <= len(body["items"])


def test_feeds_report_is_honest():
    report = build_feeds_report()
    assert report.total_count == len(report.feeds) == 9
    feed_ids = {f.id for f in report.feeds}
    assert {"treasury", "saps", "dws", "census", "agsa"} <= feed_ids
    statuses = {f.status for f in report.feeds}
    assert statuses <= {"live", "cached", "curated", "seed"}
    assert "Seed" in report.honesty_note


def test_feeds_endpoint():
    res = client.get("/feeds")
    assert res.status_code == 200
    assert res.json()["total_count"] == 9


def test_decision_register_orders_overdue_first():
    reg = build_decision_register("CPT")
    assert reg.decisions
    assert reg.decisions[0].status == "overdue"
    assert reg.overdue_count >= 1
    assert reg.open_count >= reg.overdue_count


def test_decisions_endpoint():
    res = client.get("/decisions")
    assert res.status_code == 200
    body = res.json()
    assert body["municipality"] == "CPT"
    linked = [d for d in body["decisions"] if d["linked_risk_id"]]
    assert linked, "decisions should link back to risks"


def test_ttl_cache_roundtrip():
    cache_clear()
    assert cache_get("k", 60) is None
    cache_set("k", {"v": 1})
    assert cache_get("k", 60) == {"v": 1}
    assert cache_get("k", 0) is None  # ttl 0 => expired immediately
    cache_clear()


def test_brief_is_cached_between_calls():
    cache_clear()
    first = client.get("/brief").json()
    second = client.get("/brief").json()
    # Cached copy: identical narrative without re-invoking the LLM pipeline.
    assert first["strategic_summary"] == second["strategic_summary"]
    assert first["health_score"] == second["health_score"]
    cache_clear()
