from striops.opportunity_engine import find_opportunities


def test_underspend_detected(seed_data):
    service_areas, metrics, budgets = seed_data
    opps = find_opportunities(service_areas, metrics, budgets)
    zar = [o for o in opps if o.unit == "ZAR"]
    assert zar, "expected budget underspend opportunities from seed"
    # Roads and Water are materially underspent in the seed data.
    assert any("water" in o.title.lower() or "roads" in o.title.lower() for o in zar)


def test_opportunities_have_action_and_evidence(seed_data):
    service_areas, metrics, budgets = seed_data
    for o in find_opportunities(service_areas, metrics, budgets):
        assert o.action
        assert o.evidence
        assert 0 <= o.confidence <= 1


def test_improving_metric_yields_efficiency_opportunity(seed_data):
    service_areas, metrics, budgets = seed_data
    opps = find_opportunities(service_areas, metrics, budgets)
    assert any(o.unit == "capacity" for o in opps)
