"""The Strategic Twin — a continuously-updated graph of the organisation.

Entities (wards, budgets, assets, departments...) and their relationships,
events, predictions and risks. Behind a `GraphStore` interface so the backing
store (Neo4j today) stays swappable.
"""
from helm.knowledge_graph.twin import (
    GraphStore,
    InMemoryGraphStore,
    Neo4jGraphStore,
    get_graph_store,
)

__all__ = ["GraphStore", "Neo4jGraphStore", "InMemoryGraphStore", "get_graph_store"]
