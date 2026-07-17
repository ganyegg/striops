-- Helm AI — Postgres bootstrap
-- Runs once on first container start (docker-entrypoint-initdb.d).

CREATE EXTENSION IF NOT EXISTS vector;

-- Entities: the normalized "facts" side of the Strategic Twin.
CREATE TABLE IF NOT EXISTS entities (
    id           TEXT PRIMARY KEY,
    entity_type  TEXT NOT NULL,
    name         TEXT NOT NULL,
    properties   JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding    vector(768),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities (entity_type);

-- Metric time series feeding forecasts / risk trend.
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

-- Budget vs actual (Municipal Money) — kept separate for clarity.
CREATE TABLE IF NOT EXISTS budget_lines (
    id            BIGSERIAL PRIMARY KEY,
    function_name TEXT NOT NULL,
    financial_year INT NOT NULL,
    budget        DOUBLE PRECISION NOT NULL,
    actual        DOUBLE PRECISION NOT NULL,
    source        TEXT,
    UNIQUE (function_name, financial_year)
);

-- Strategic Memory: every decision + its outcomes over time.
CREATE TABLE IF NOT EXISTS decisions (
    id           BIGSERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT,
    decided_at   DATE NOT NULL DEFAULT CURRENT_DATE,
    payload      JSONB NOT NULL DEFAULT '{}'::jsonb,
    outcome      JSONB
);
