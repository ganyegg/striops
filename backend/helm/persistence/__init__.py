"""Persistence: the facts store (Postgres) with a seed-data fallback.

Read APIs return domain models so engines/agents never touch SQL. If Postgres
is unreachable or empty, the repository transparently serves the committed seed
datasets so the platform always produces a brief.
"""
from helm.persistence.repository import Repository, get_repository

__all__ = ["Repository", "get_repository"]
