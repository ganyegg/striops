"""Deep-dive domain profiles + provenance, and the municipality registry.

Each domain (fiscal, staffing, housing, safety, policies, ...) is a
provenance-first `DomainProfile`: every indicator resolves to a public source
so figures are verifiable. The same domain adapters run for every municipality,
which is how Helm AI replicates across metros and, eventually, nationally.
"""
from helm.domains.registry import DOMAIN_CATALOG, domain_catalog
from helm.domains.service import (
    get_domain,
    get_municipality,
    list_domains,
    list_municipalities,
)

__all__ = [
    "DOMAIN_CATALOG",
    "domain_catalog",
    "list_municipalities",
    "get_municipality",
    "list_domains",
    "get_domain",
]
