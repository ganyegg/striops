"""Facts repository.

`Repository` reads/writes the normalized facts (entities, metrics, budget
lines). It prefers Postgres; if Postgres is unreachable or has not been
populated yet, it falls back to the committed seed datasets so the reasoning
core always has something to reason over.
"""
from __future__ import annotations

import json
from datetime import date, datetime

from striops.core.config import Settings, get_settings
from striops.core.logging import get_logger
from striops.core.models import (
    BudgetLine,
    Entity,
    EntityType,
    MetricPoint,
    MetricSeries,
)
from striops.core.paths import seed_dir

log = get_logger("striops.persistence")


def _load_seed(name: str) -> list[dict]:
    path = seed_dir() / name
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _parse_period(value) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


class Repository:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._conn = None
        self._use_pg = False
        self._connect()

    # ---- connection -----------------------------------------------------
    def _connect(self) -> None:
        try:
            import psycopg

            self._conn = psycopg.connect(self.settings.postgres_dsn, autocommit=True)
            with self._conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.entities')")
                exists = cur.fetchone()[0]
            self._use_pg = exists is not None
            if self._use_pg:
                log.info("repository using postgres")
        except Exception as exc:
            log.warning("postgres unavailable, using seed data", extra={"context": {"error": str(exc)}})
            self._use_pg = False

    @property
    def backend(self) -> str:
        return "postgres" if self._use_pg else "seed"

    def has_data(self) -> bool:
        return len(self.service_areas()) > 0

    # ---- reads ----------------------------------------------------------
    def service_areas(self) -> list[Entity]:
        if self._use_pg:
            rows = self._query(
                "SELECT id, name, properties FROM entities WHERE entity_type = %s",
                (EntityType.SERVICE_AREA.value,),
            )
            if rows:
                return [
                    Entity(id=r[0], type=EntityType.SERVICE_AREA, name=r[1], properties=r[2] or {})
                    for r in rows
                ]
        return [
            Entity(
                id=d["id"],
                type=EntityType.SERVICE_AREA,
                name=d["name"],
                properties={k: v for k, v in d.items() if k not in ("id", "name")},
            )
            for d in _load_seed("service_areas.json")
        ]

    def wards(self) -> list[Entity]:
        if self._use_pg:
            rows = self._query(
                "SELECT id, name, properties FROM entities WHERE entity_type = %s",
                (EntityType.WARD.value,),
            )
            if rows:
                return [
                    Entity(id=r[0], type=EntityType.WARD, name=r[1], properties=r[2] or {})
                    for r in rows
                ]
        return [
            Entity(
                id=d["id"],
                type=EntityType.WARD,
                name=d.get("ward_name", d["id"]),
                properties={k: v for k, v in d.items() if k not in ("id",)},
            )
            for d in _load_seed("wards.json")
        ]

    def metric_series(self) -> list[MetricSeries]:
        if self._use_pg:
            rows = self._query(
                "SELECT entity_id, metric, unit, period, value FROM metrics ORDER BY entity_id, metric, period",
            )
            if rows:
                grouped: dict[tuple[str, str], MetricSeries] = {}
                for entity_id, metric, unit, period, value in rows:
                    key = (entity_id, metric)
                    if key not in grouped:
                        grouped[key] = MetricSeries(entity_id=entity_id, metric=metric, unit=unit)
                    grouped[key].points.append(MetricPoint(period=period, value=value))
                return list(grouped.values())
        out: list[MetricSeries] = []
        for d in _load_seed("metrics.json"):
            out.append(
                MetricSeries(
                    entity_id=d["entity_id"],
                    metric=d["metric"],
                    unit=d.get("unit"),
                    points=[
                        MetricPoint(period=_parse_period(p["period"]), value=p["value"])
                        for p in d["points"]
                    ],
                )
            )
        return out

    def budget_lines(self) -> list[BudgetLine]:
        if self._use_pg:
            rows = self._query(
                "SELECT function_name, financial_year, budget, actual, source FROM budget_lines ORDER BY function_name, financial_year",
            )
            if rows:
                return [
                    BudgetLine(
                        function_name=r[0], financial_year=r[1], budget=r[2], actual=r[3], source=r[4]
                    )
                    for r in rows
                ]
        return [BudgetLine(**d) for d in _load_seed("budget_lines.json")]

    # ---- writes (used by ingestion) ------------------------------------
    def upsert_entity(self, entity: Entity, embedding: list[float] | None = None) -> None:
        if not self._use_pg:
            return
        self._exec(
            """
            INSERT INTO entities (id, entity_type, name, properties, embedding, updated_at)
            VALUES (%s, %s, %s, %s, %s, now())
            ON CONFLICT (id) DO UPDATE
              SET name = EXCLUDED.name, properties = EXCLUDED.properties,
                  embedding = EXCLUDED.embedding, updated_at = now()
            """,
            (
                entity.id,
                entity.type.value,
                entity.name,
                json.dumps(entity.properties),
                embedding,
            ),
        )

    def upsert_metric(self, series: MetricSeries) -> None:
        if not self._use_pg:
            return
        for p in series.points:
            self._exec(
                """
                INSERT INTO metrics (entity_id, metric, period, value, unit, source)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (entity_id, metric, period) DO UPDATE SET value = EXCLUDED.value
                """,
                (series.entity_id, series.metric, p.period, p.value, series.unit, "ingest"),
            )

    def upsert_budget_line(self, line: BudgetLine) -> None:
        if not self._use_pg:
            return
        self._exec(
            """
            INSERT INTO budget_lines (function_name, financial_year, budget, actual, source)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (function_name, financial_year) DO UPDATE
              SET budget = EXCLUDED.budget, actual = EXCLUDED.actual
            """,
            (line.function_name, line.financial_year, line.budget, line.actual, line.source or "ingest"),
        )

    def mark_populated(self) -> None:
        """Re-check whether Postgres now has data (after ingestion)."""
        self._use_pg = self._use_pg or self._conn is not None

    # ---- low-level ------------------------------------------------------
    def _query(self, sql: str, params: tuple = ()) -> list[tuple]:
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def _exec(self, sql: str, params: tuple = ()) -> None:
        with self._conn.cursor() as cur:
            cur.execute(sql, params)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()


_repository: Repository | None = None


def get_repository(settings: Settings | None = None) -> Repository:
    global _repository
    if _repository is None:
        _repository = Repository(settings)
    return _repository
