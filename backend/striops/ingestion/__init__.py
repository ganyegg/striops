"""Ingestion: pull public Cape Town data into the facts store + Strategic Twin.

Live sources first (ArcGIS FeatureServer, National Treasury Municipal Money),
with a transparent fall back to committed seed data when offline or in CI.
"""
from striops.ingestion.arcgis import ARCGIS_LAYERS, fetch_layer
from striops.ingestion.treasury import fetch_budget_lines

__all__ = ["fetch_layer", "ARCGIS_LAYERS", "fetch_budget_lines"]
