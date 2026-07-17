"""Strategic Twin graph store.

`GraphStore` is the interface. `Neo4jGraphStore` persists to Neo4j.
`InMemoryGraphStore` keeps everything in a dict — used by tests and as a safe
fallback when Neo4j is unavailable so the platform never hard-fails on the graph.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from helm.core.config import Settings, get_settings
from helm.core.logging import get_logger
from helm.core.models import Entity

log = get_logger("helm.knowledge_graph")


class GraphStore(ABC):
    @abstractmethod
    def upsert_entity(self, entity: Entity) -> None: ...

    @abstractmethod
    def relate(self, src_id: str, rel: str, dst_id: str, props: dict | None = None) -> None: ...

    @abstractmethod
    def get_entity(self, entity_id: str) -> Entity | None: ...

    @abstractmethod
    def neighbors(self, entity_id: str) -> list[Entity]: ...

    @abstractmethod
    def count(self) -> int: ...

    def close(self) -> None:  # pragma: no cover - default no-op
        pass


class InMemoryGraphStore(GraphStore):
    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._edges: list[tuple[str, str, str, dict]] = []

    def upsert_entity(self, entity: Entity) -> None:
        self._entities[entity.id] = entity

    def relate(self, src_id: str, rel: str, dst_id: str, props: dict | None = None) -> None:
        self._edges.append((src_id, rel, dst_id, props or {}))

    def get_entity(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def neighbors(self, entity_id: str) -> list[Entity]:
        ids = {dst for src, _, dst, _ in self._edges if src == entity_id}
        ids |= {src for src, _, dst, _ in self._edges if dst == entity_id}
        return [self._entities[i] for i in ids if i in self._entities]

    def count(self) -> int:
        return len(self._entities)


class Neo4jGraphStore(GraphStore):
    def __init__(self, settings: Settings) -> None:
        from neo4j import GraphDatabase

        self._driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
        try:
            self._driver.verify_connectivity()
        except Exception:
            # Close the half-open driver so we don't leak it via the destructor.
            self._driver.close()
            raise

    def upsert_entity(self, entity: Entity) -> None:
        with self._driver.session() as session:
            session.run(
                """
                MERGE (e:Entity {id: $id})
                SET e.name = $name, e.type = $type, e += $props
                """,
                id=entity.id,
                name=entity.name,
                type=entity.type.value,
                props={k: v for k, v in entity.properties.items() if isinstance(v, (str | int | float | bool))},
            )

    def relate(self, src_id: str, rel: str, dst_id: str, props: dict | None = None) -> None:
        rel = "".join(c for c in rel.upper() if c.isalnum() or c == "_") or "RELATED_TO"
        with self._driver.session() as session:
            session.run(
                f"""
                MATCH (a:Entity {{id: $src}})
                MATCH (b:Entity {{id: $dst}})
                MERGE (a)-[r:{rel}]->(b)
                SET r += $props
                """,
                src=src_id,
                dst=dst_id,
                props=props or {},
            )

    def get_entity(self, entity_id: str) -> Entity | None:
        with self._driver.session() as session:
            rec = session.run(
                "MATCH (e:Entity {id: $id}) RETURN e", id=entity_id
            ).single()
            if not rec:
                return None
            return self._to_entity(dict(rec["e"]))

    def neighbors(self, entity_id: str) -> list[Entity]:
        with self._driver.session() as session:
            result = session.run(
                "MATCH (e:Entity {id: $id})-[]-(n:Entity) RETURN DISTINCT n",
                id=entity_id,
            )
            return [self._to_entity(dict(r["n"])) for r in result]

    def count(self) -> int:
        with self._driver.session() as session:
            rec = session.run("MATCH (e:Entity) RETURN count(e) AS c").single()
            return int(rec["c"]) if rec else 0

    def close(self) -> None:
        self._driver.close()

    @staticmethod
    def _to_entity(node: dict) -> Entity:
        from helm.core.models import EntityType

        etype = node.pop("type", "Asset")
        name = node.pop("name", node.get("id", "unknown"))
        eid = node.pop("id")
        try:
            etype_enum = EntityType(etype)
        except ValueError:
            etype_enum = EntityType.ASSET
        return Entity(id=eid, type=etype_enum, name=name, properties=node)


_store: GraphStore | None = None


def get_graph_store(settings: Settings | None = None) -> GraphStore:
    """Return the process-wide graph store (Neo4j if reachable, else in-memory)."""
    global _store
    if _store is not None:
        return _store
    settings = settings or get_settings()
    try:
        _store = Neo4jGraphStore(settings)
        log.info("graph store ready", extra={"context": {"store": "neo4j"}})
    except Exception as exc:
        log.warning("neo4j unavailable, using in-memory graph", extra={"context": {"error": str(exc)}})
        _store = InMemoryGraphStore()
    return _store
