"""Ingestion pipeline: public data -> Postgres facts + Neo4j Strategic Twin.

Run as a one-shot job (nightly-capable):  python -m striops.ingestion.pipeline
"""
from __future__ import annotations

import json

from striops.core.config import get_settings
from striops.core.logging import configure_logging, get_logger
from striops.core.models import Entity, EntityType, MetricPoint, MetricSeries
from striops.core.paths import seed_dir
from striops.ingestion.arcgis import ARCGIS_LAYERS, fetch_layer
from striops.ingestion.coct_opendata import fetch_live_series
from striops.ingestion.treasury import fetch_budget_lines
from striops.knowledge_graph import get_graph_store
from striops.persistence import get_repository
from striops.persistence.schema import ensure_schema
from striops.reasoning import get_llm

log = get_logger("striops.ingestion.pipeline")


def _load_seed(name: str) -> list[dict]:
    path = seed_dir() / name
    return json.loads(path.read_text()) if path.exists() else []


def _ward_entities() -> list[Entity]:
    """Prefer live ArcGIS wards; fall back to seed."""
    features = fetch_layer(ARCGIS_LAYERS["wards"], include_geometry=False)
    entities: list[Entity] = []
    for f in features:
        key = f.get("SL_WARD_KEY") or f.get("OBJECTID")
        name = f.get("WARD_NAME") or (f"Ward {key}" if key else None)
        if key is None or name is None:
            continue
        entities.append(
            Entity(
                id=f"ward-{key}",
                type=EntityType.WARD,
                name=name,
                properties={"sub_council": f.get("SL_SUB_CNCL_KEY"), "year": f.get("WARD_YEAR"), "source": "arcgis"},
            )
        )
    if entities:
        log.info("wards from arcgis", extra={"context": {"count": len(entities)}})
        return entities
    return [
        Entity(
            id=d["id"],
            type=EntityType.WARD,
            name=d.get("ward_name", d["id"]),
            properties={k: v for k, v in d.items() if k != "id"},
        )
        for d in _load_seed("wards.json")
    ]


def run() -> dict:
    settings = get_settings()
    configure_logging(settings.striops_log_level)
    # Create the schema first so a freshly-provisioned managed Postgres is
    # writable (otherwise the repository stays on seed and writes no-op).
    ensure_schema(settings)
    repo = get_repository(settings)
    graph = get_graph_store(settings)
    llm = get_llm(settings)

    counts = {"wards": 0, "service_areas": 0, "metrics": 0, "budget_lines": 0}

    # 1) Wards
    for ward in _ward_entities():
        _upsert(repo, graph, llm, ward)
        counts["wards"] += 1

    # 2) Service areas (curated domain entities)
    service_areas: list[Entity] = []
    for d in _load_seed("service_areas.json"):
        ent = Entity(
            id=d["id"],
            type=EntityType.SERVICE_AREA,
            name=d["name"],
            properties={k: v for k, v in d.items() if k not in ("id", "name")},
        )
        service_areas.append(ent)
        _upsert(repo, graph, llm, ent)
        counts["service_areas"] += 1

    # 3) Metrics — seed baseline first, then overlay live public feeds so the
    #    freshest measured values win (same (entity,metric,period) key upserts).
    for d in _load_seed("metrics.json"):
        series = MetricSeries(
            entity_id=d["entity_id"],
            metric=d["metric"],
            unit=d.get("unit"),
            points=[MetricPoint(period=p["period"], value=p["value"]) for p in d["points"]],
        )
        repo.upsert_metric(series)
        counts["metrics"] += 1

    # 3b) Live public feeds (City of Cape Town Open Data Portal). Best-effort:
    #     each connector falls back to its cache and never breaks ingestion.
    counts["live_series"] = 0
    for series in fetch_live_series():
        repo.upsert_metric(series)
        counts["live_series"] += 1
        log.info(
            "live series ingested",
            extra={"context": {"metric": f"{series.entity_id}/{series.metric}", "points": len(series.points)}},
        )

    # 4) Budget lines + BudgetItem entities, related to their service area.
    for line in fetch_budget_lines(settings.striops_municipality):
        repo.upsert_budget_line(line)
        counts["budget_lines"] += 1
        item = Entity(
            id=f"budget-{line.function_name.lower().replace(' ', '-')}-{line.financial_year}",
            type=EntityType.BUDGET_ITEM,
            name=f"{line.function_name} FY{line.financial_year}",
            properties={
                "function": line.function_name,
                "financial_year": line.financial_year,
                "budget": line.budget,
                "actual": line.actual,
            },
        )
        _upsert(repo, graph, llm, item)
        owner = next((s for s in service_areas if s.properties.get("budget_function") == line.function_name), None)
        if owner:
            graph.relate(owner.id, "FUNDED_BY", item.id, {"year": line.financial_year})

    log.info("ingestion complete", extra={"context": {**counts, "graph_nodes": graph.count(), "facts_backend": repo.backend}})
    return counts


def _upsert(repo, graph, llm, entity: Entity) -> None:
    embedding = None
    try:
        embedding = llm.embed(f"{entity.type.value}: {entity.name}")
    except Exception:
        embedding = None
    repo.upsert_entity(entity, embedding=embedding)
    try:
        graph.upsert_entity(entity)
    except Exception as exc:  # pragma: no cover
        log.warning("graph upsert failed", extra={"context": {"id": entity.id, "error": str(exc)}})


if __name__ == "__main__":
    run()
