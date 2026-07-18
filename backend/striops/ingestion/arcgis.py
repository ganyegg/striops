"""Generic City of Cape Town ArcGIS FeatureServer puller.

Service: Theme_Based/Open_Data_Service (FeatureServer). Layer IDs verified from
the City's open data service. We paginate with resultOffset and cache raw
responses so re-runs are offline-friendly and auditable.
"""
from __future__ import annotations

import json

import httpx

from striops.core.logging import get_logger
from striops.core.paths import cache_dir

log = get_logger("striops.ingestion.arcgis")

ARCGIS_BASE = (
    "https://citymaps.capetown.gov.za/agsext/rest/services/"
    "Theme_Based/Open_Data_Service/FeatureServer"
)

# Verified layer IDs from the City of Cape Town Open Data Service.
ARCGIS_LAYERS: dict[str, int] = {
    "wards": 78,
    "refuse_collection_beats": 136,
    "landfill_sites": 102,
    "electricity_districts": 4,
}

_PAGE_SIZE = 1000


def fetch_layer(
    layer_id: int,
    *,
    out_fields: str = "*",
    where: str = "1=1",
    include_geometry: bool = False,
    timeout: float = 20.0,
    use_cache: bool = True,
) -> list[dict]:
    """Return a list of feature attribute dicts for an ArcGIS layer.

    Falls back to a cached copy on any network error so ingestion never hard-fails.
    """
    cache_path = cache_dir() / f"arcgis_layer_{layer_id}.json"
    features: list[dict] = []
    offset = 0
    try:
        with httpx.Client(timeout=timeout) as client:
            while True:
                params = {
                    "where": where,
                    "outFields": out_fields,
                    "returnGeometry": str(include_geometry).lower(),
                    "resultOffset": offset,
                    "resultRecordCount": _PAGE_SIZE,
                    "f": "json",
                }
                resp = client.get(f"{ARCGIS_BASE}/{layer_id}/query", params=params)
                resp.raise_for_status()
                data = resp.json()
                page = [f.get("attributes", {}) for f in data.get("features", [])]
                features.extend(page)
                if len(page) < _PAGE_SIZE or not data.get("exceededTransferLimit"):
                    break
                offset += _PAGE_SIZE
        cache_path.write_text(json.dumps(features))
        log.info("arcgis layer fetched", extra={"context": {"layer": layer_id, "count": len(features)}})
        return features
    except Exception as exc:
        log.warning(
            "arcgis fetch failed, trying cache",
            extra={"context": {"layer": layer_id, "error": str(exc)}},
        )
        if use_cache and cache_path.exists():
            return json.loads(cache_path.read_text())
        return []
