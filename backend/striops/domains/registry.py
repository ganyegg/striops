"""Municipality registry + canonical domain catalog.

The catalog is the fixed list of deep-dive domains Striops covers. The registry
is the set of municipalities we serve (metros first), loaded from seed config.
Both are municipality-agnostic: adding a metro is data, not code.
"""
from __future__ import annotations

import json

from striops.core.models import DomainCatalogEntry, DomainId, Municipality
from striops.core.paths import seed_dir

# Canonical deep-dive domains. `order` controls tab ordering in the UI.
DOMAIN_CATALOG: list[DomainCatalogEntry] = [
    DomainCatalogEntry(id=DomainId.FISCAL, name="Fiscal Health", order=10, icon="scale",
                       description="Solvency, cash, audit outcomes, revenue and collection."),
    DomainCatalogEntry(id=DomainId.BUDGET, name="Budget", order=20, icon="wallet",
                       description="Adopted budget, capital vs operating, in-year spend."),
    DomainCatalogEntry(id=DomainId.STAFFING, name="Staffing", order=30, icon="users",
                       description="Headcount, vacancies, employee-cost ratio, overtime."),
    DomainCatalogEntry(id=DomainId.HOUSING_POPULATION, name="Housing & Population", order=40, icon="home",
                       description="Population pressure, housing delivery and backlog."),
    DomainCatalogEntry(id=DomainId.SAFETY_POLICING, name="Safety & Policing", order=50, icon="shield",
                       description="Crime statistics, metro police and law enforcement."),
    DomainCatalogEntry(id=DomainId.GOVERNANCE_POLICIES, name="Governance & Policies", order=60, icon="landmark",
                       description="IDP, by-laws, policy commitments and reforms."),
    DomainCatalogEntry(id=DomainId.WATER, name="Water & Sanitation", order=70, icon="droplet",
                       description="Dam levels, non-revenue water, sanitation."),
    DomainCatalogEntry(id=DomainId.ENERGY, name="Energy", order=80, icon="zap",
                       description="Electricity supply, load-shedding mitigation, grid spend."),
    DomainCatalogEntry(id=DomainId.WASTE, name="Waste", order=90, icon="trash",
                       description="Collection coverage, landfill airspace, cleanliness."),
    DomainCatalogEntry(id=DomainId.TRANSPORT, name="Roads & Transport", order=100, icon="road",
                       description="Road condition, maintenance backlog, public transport."),
    DomainCatalogEntry(id=DomainId.ECONOMY_JOBS, name="Economy & Jobs", order=110, icon="trending",
                       description="Unemployment, GDP contribution, investment."),
    DomainCatalogEntry(id=DomainId.HEALTH, name="Health", order=120, icon="heart",
                       description="Clinic access, environmental health, outbreaks."),
    DomainCatalogEntry(id=DomainId.ENVIRONMENT, name="Environment & Climate", order=130, icon="leaf",
                       description="Air quality, coastal management, climate resilience."),
    DomainCatalogEntry(id=DomainId.SERVICE_DELIVERY, name="Service Delivery", order=140, icon="inbox",
                       description="Complaint (C3) notifications, resolution times."),
]

_CATALOG_BY_ID = {e.id: e for e in DOMAIN_CATALOG}


def domain_catalog() -> list[DomainCatalogEntry]:
    return sorted(DOMAIN_CATALOG, key=lambda e: e.order)


def catalog_entry(domain_id: DomainId) -> DomainCatalogEntry | None:
    return _CATALOG_BY_ID.get(domain_id)


def load_municipalities() -> list[Municipality]:
    path = seed_dir() / "municipalities.json"
    if not path.exists():
        return []
    return [Municipality(**m) for m in json.loads(path.read_text())]
