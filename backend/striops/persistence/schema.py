"""Idempotent Postgres schema bootstrap.

A freshly-provisioned managed Postgres (e.g. Neon) is empty, so the
Repository would fall back to seed forever. Running ``ensure_schema()`` at
ingest/startup creates the tables (and pgvector when available) so Striops can
actually read from — and the pipeline can load into — the database.

Safe to run repeatedly; every statement is ``IF NOT EXISTS``. If the ``vector``
extension is unavailable, entities are created without the embedding column and
semantic search silently degrades (all other facts work).
"""
from __future__ import annotations

from striops.core.config import Settings, get_settings
from striops.core.logging import get_logger

log = get_logger("striops.persistence.schema")

_DDL_CORE = """
CREATE TABLE IF NOT EXISTS entities (
    id           TEXT PRIMARY KEY,
    entity_type  TEXT NOT NULL,
    name         TEXT NOT NULL,
    properties   JSONB NOT NULL DEFAULT '{}'::jsonb,
    __EMBEDDING_COL__
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities (entity_type);

CREATE TABLE IF NOT EXISTS metrics (
    id           BIGSERIAL PRIMARY KEY,
    entity_id    TEXT REFERENCES entities (id) ON DELETE CASCADE,
    metric       TEXT NOT NULL,
    period       DATE NOT NULL,
    value        DOUBLE PRECISION NOT NULL,
    unit         TEXT,
    source       TEXT,
    UNIQUE (entity_id, metric, period)
);
CREATE INDEX IF NOT EXISTS idx_metrics_entity_metric ON metrics (entity_id, metric);

CREATE TABLE IF NOT EXISTS budget_lines (
    id            BIGSERIAL PRIMARY KEY,
    function_name TEXT NOT NULL,
    financial_year INT NOT NULL,
    budget        DOUBLE PRECISION NOT NULL,
    actual        DOUBLE PRECISION NOT NULL,
    source        TEXT,
    UNIQUE (function_name, financial_year)
);
"""


def ensure_schema(settings: Settings | None = None) -> bool:
    """Create the Striops schema if absent. Returns True if Postgres is ready."""
    settings = settings or get_settings()
    try:
        import psycopg
    except Exception as exc:  # driver missing
        log.warning("psycopg unavailable; cannot bootstrap schema", extra={"context": {"error": str(exc)}})
        return False

    try:
        with psycopg.connect(settings.postgres_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                has_vector = False
                try:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    has_vector = True
                except Exception as exc:
                    log.warning("pgvector unavailable; embeddings disabled", extra={"context": {"error": str(exc)}})
                embedding_col = "embedding    vector(768)," if has_vector else ""
                cur.execute(_DDL_CORE.replace("__EMBEDDING_COL__", embedding_col))
        log.info("schema ensured", extra={"context": {"pgvector": has_vector}})
        return True
    except Exception as exc:
        log.warning("schema bootstrap failed; staying on seed", extra={"context": {"error": str(exc)}})
        return False
