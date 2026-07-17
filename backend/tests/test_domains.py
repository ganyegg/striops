import pytest
from fastapi.testclient import TestClient

from helm.api.main import app
from helm.core.models import VerificationStatus
from helm.domains import (
    domain_catalog,
    get_domain,
    get_municipality,
    list_domains,
    list_municipalities,
)
from helm.domains.service import _profiles

client = TestClient(app)


def test_registry_has_metros():
    munis = list_municipalities()
    codes = {m.code for m in munis}
    assert {"CPT", "JHB", "ETH", "TSH", "EKU", "NMA", "BUF", "MAN"} <= codes
    assert get_municipality("cpt").status == "live"


def test_catalog_covers_named_domains():
    ids = {e.id.value for e in domain_catalog()}
    for required in [
        "fiscal", "budget", "staffing", "housing_population",
        "safety_policing", "governance_policies",
    ]:
        assert required in ids


def test_cpt_domains_availability():
    rows = list_domains("CPT")
    available = {r["id"] for r in rows if r["available"]}
    assert "budget" in available and "fiscal" in available and "safety_policing" in available
    # A roadmap domain is listed but not available for CPT yet.
    transport = next(r for r in rows if r["id"] == "transport")
    assert transport["available"] is False


def test_every_indicator_resolves_to_a_source():
    """Provenance integrity: no dangling source references across all profiles."""
    profiles = _profiles("CPT")
    assert profiles
    for profile in profiles.values():
        source_ids = {s.id for s in profile.sources}
        for ind in profile.indicators:
            assert ind.source_id in source_ids, f"{profile.id}:{ind.key}"
        for pol in profile.policies:
            assert pol.source_id in source_ids


def test_verified_indicators_have_source_urls():
    profiles = _profiles("CPT")
    for profile in profiles.values():
        by_id = {s.id: s for s in profile.sources}
        for ind in profile.indicators:
            if ind.verification == VerificationStatus.VERIFIED:
                assert by_id[ind.source_id].url.startswith("http")


def test_budget_profile_is_mostly_verified():
    profile = get_domain("CPT", "budget")
    assert profile.verified_share >= 0.9
    total = next(i for i in profile.indicators if i.key == "total")
    assert total.value == "R87.79bn"


def test_get_unavailable_domain_raises():
    with pytest.raises(KeyError):
        get_domain("CPT", "transport")


def test_api_municipalities():
    r = client.get("/municipalities")
    assert r.status_code == 200
    assert any(m["code"] == "CPT" for m in r.json())


def test_api_municipality_domains():
    r = client.get("/municipalities/CPT/domains")
    assert r.status_code == 200
    assert any(d["available"] for d in r.json())


def test_api_domain_profile():
    r = client.get("/municipalities/CPT/domains/fiscal")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "fiscal"
    assert body["indicators"]
    assert body["sources"]


def test_api_unknown_municipality_404():
    assert client.get("/municipalities/ZZZ").status_code == 404


def test_api_unavailable_domain_404():
    assert client.get("/municipalities/CPT/domains/transport").status_code == 404
