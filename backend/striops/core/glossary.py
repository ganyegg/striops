"""Plain-language explainers for metrics, risks and initiatives.

Written so a Mayor, MMC or resident can understand the term in one breath —
then the number, then the action.
"""
from __future__ import annotations

GLOSSARY: dict[str, dict[str, str]] = {
    "non_revenue_water_pct": {
        "term": "Non-revenue water",
        "definition": (
            "Water that the City produces and pumps into the network but never bills for — "
            "mostly lost to leaks, bursts, theft, or metering gaps. High non-revenue water "
            "means you pay to treat and move water that never reaches a paying customer."
        ),
        "in_one_line": "Water lost or unbilled after it enters the pipes.",
    },
    "refuse_service_requests": {
        "term": "Refuse service requests",
        "definition": (
            "Complaints and service tickets about missed collections, illegal dumping, "
            "or overflowing bins. A rising trend usually means collection capacity is "
            "falling behind household demand."
        ),
        "in_one_line": "How often residents report waste-collection problems.",
    },
    "road_maintenance_backlog_km": {
        "term": "Road maintenance backlog",
        "definition": (
            "Kilometres of road that need resurfacing or repair but have not yet been done. "
            "A growing backlog means potholes and stormwater failures will keep compounding "
            "faster than the current capital run-rate can fix."
        ),
        "in_one_line": "Roads waiting for repair that haven’t been fixed yet.",
    },
    "public_lighting_outages": {
        "term": "Public lighting outages",
        "definition": (
            "Streetlights and public lights reported as not working. Dark streets reduce "
            "perceived safety and make waiting for transport after dark more dangerous."
        ),
        "in_one_line": "How many public lights are reported broken.",
    },
    "library_visits": {
        "term": "Library visits",
        "definition": (
            "Footfall at City libraries. Declining visits can signal service quality issues, "
            "safety concerns around facilities, or that digital alternatives are winning — "
            "either way it is a citizen-experience signal."
        ),
        "in_one_line": "How many people are using City libraries.",
    },
    "dam_storage": {
        "term": "Dam storage",
        "definition": (
            "How full the Western Cape Water Supply System dams are, as a percentage of "
            "capacity. This is the City’s bulk water ‘bank balance’ heading into summer."
        ),
        "in_one_line": "How full Cape Town’s major dams are.",
    },
    "system_energy_kwh": {
        "term": "System energy sent out",
        "definition": (
            "Total electricity (kWh) delivered across the City’s network in the month — "
            "Eskom supply plus own generation, net of losses. It tracks demand, economic "
            "activity, and the load the grid must carry through peak season."
        ),
        "in_one_line": "How much electricity the City moved this month.",
    },
    "electricity_billed_kwh": {
        "term": "Electricity billed",
        "definition": (
            "Total electricity (kWh) billed to customers across suburbs in the month. "
            "Read against system energy sent out, the gap hints at losses, non-payment, "
            "or metering issues; it is also a revenue and economic-activity signal."
        ),
        "in_one_line": "How much electricity the City billed for this month.",
    },
    "municipal_arrears_zar": {
        "term": "Municipal arrears",
        "definition": (
            "The total rand value residents and businesses owe the City in overdue "
            "accounts (rates and services). A rising balance strains cash flow and is a "
            "leading indicator of affordability stress and collection risk."
        ),
        "in_one_line": "How much money is owed to the City in overdue bills.",
    },
    "clinic_waiting_days": {
        "term": "Clinic waiting days",
        "definition": (
            "Median days residents wait for a City primary-health clinic appointment or "
            "service. Rising waits mean access is eroding before people reach a clinician."
        ),
        "in_one_line": "How long people wait for a City clinic.",
    },
    "ems_response_minutes": {
        "term": "EMS response time",
        "definition": (
            "Average minutes for emergency medical services to reach a Priority-1 call. "
            "Minutes above an urban benchmark mean lives are waiting on the road."
        ),
        "in_one_line": "How fast ambulances reach life-threatening calls.",
    },
    "leap": {
        "term": "LEAP",
        "definition": (
            "Law Enforcement Advancement Plan — additional law-enforcement officers deployed "
            "into high-crime precincts, funded with provincial support, to reduce murders "
            "and contact crime where they concentrate."
        ),
        "in_one_line": "Extra officers placed in the City’s toughest crime hotspots.",
    },
}


def explain(metric_or_key: str) -> dict[str, str] | None:
    return GLOSSARY.get(metric_or_key)


def explain_risk_id(risk_id: str) -> dict[str, str] | None:
    for key in GLOSSARY:
        if risk_id.endswith(key) or key in risk_id:
            return GLOSSARY[key]
    return None
