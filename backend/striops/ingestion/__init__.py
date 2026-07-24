"""Ingestion: pull public municipal + national data into facts + Strategic Twin.

Live sources first (CoCT ODP, Treasury, SAPS, DWS, Census, AGSA), with a
transparent fall back to committed seed data when offline or in CI.
"""
from striops.ingestion.arcgis import ARCGIS_LAYERS, fetch_layer
from striops.ingestion.national import apply_national_overlays, fetch_national_series
from striops.ingestion.treasury import fetch_budget_lines

__all__ = [
    "fetch_layer",
    "ARCGIS_LAYERS",
    "fetch_budget_lines",
    "fetch_national_series",
    "apply_national_overlays",
]
