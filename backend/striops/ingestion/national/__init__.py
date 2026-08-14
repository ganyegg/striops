"""National (multi-municipality) public data connectors.

Each connector is best-effort: caches on success, falls back to seed/cache,
and never raises out of ``fetch_national_series``.
"""
from __future__ import annotations

from striops.core.models import MetricSeries
from striops.ingestion.national.audit_opinions import fetch_audit_overlay
from striops.ingestion.national.census_baselines import fetch_census_series, write_census_overlay
from striops.ingestion.national.dws_dams import fetch_dws_dam_series
from striops.ingestion.national.saps_crime import fetch_crime_series, write_crime_overlay

__all__ = [
    "fetch_national_series",
    "apply_national_overlays",
]


def fetch_national_series(municipality: str = "CPT") -> list[MetricSeries]:
    """Return metric series from national sources for the active municipality."""
    series: list[MetricSeries] = []
    for fn in (
        lambda: fetch_dws_dam_series(municipality),
        lambda: fetch_crime_series(municipality),
        lambda: fetch_census_series(municipality),
    ):
        try:
            got = fn()
            if isinstance(got, list):
                series.extend(s for s in got if s is not None)
            elif got is not None:
                series.append(got)
        except Exception:
            continue
    return series


def apply_national_overlays(municipality: str = "CPT") -> dict[str, bool]:
    """Write domain-overlay JSON patches (audit, census, crime headlines)."""
    results = {"audit": False, "census": False, "crime": False}
    try:
        results["audit"] = bool(fetch_audit_overlay(municipality))
    except Exception:
        pass
    try:
        results["census"] = bool(write_census_overlay(municipality))
    except Exception:
        pass
    try:
        results["crime"] = bool(write_crime_overlay(municipality))
    except Exception:
        pass
    return results
