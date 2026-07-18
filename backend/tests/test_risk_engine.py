from striops.risk_engine import assess_risks


def test_seed_produces_ranked_risks(seed_data):
    service_areas, metrics, budgets = seed_data
    risks = assess_risks(service_areas, metrics, budgets)
    assert risks, "expected at least one risk from seed data"
    # Sorted descending by score.
    scores = [r.score for r in risks]
    assert scores == sorted(scores, reverse=True)


def test_risk_score_formula(seed_data):
    service_areas, metrics, budgets = seed_data
    risks = assess_risks(service_areas, metrics, budgets)
    r = risks[0]
    expected = round(r.likelihood * r.impact * r.trend * r.confidence * 100, 1)
    assert r.score == expected


def test_every_risk_has_evidence_and_owner(seed_data):
    service_areas, metrics, budgets = seed_data
    for r in assess_risks(service_areas, metrics, budgets):
        assert r.evidence, "risk must cite evidence"
        assert r.owner
        assert r.mitigation
        assert r.forecast is not None


def test_water_losses_surface_as_risk(seed_data):
    service_areas, metrics, budgets = seed_data
    titles = [r.title for r in assess_risks(service_areas, metrics, budgets)]
    assert any("water" in t.lower() for t in titles)
