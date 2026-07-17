"""Tiny in-process TTL cache for expensive builds (LLM-backed briefs).

One entry per key; thread-safe; monotonic-clock based so wall-clock jumps
don't invalidate or immortalise entries.
"""
from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_store: dict[str, tuple[float, Any]] = {}


def cache_get(key: str, ttl_seconds: float) -> Any | None:
    with _lock:
        hit = _store.get(key)
        if hit is None:
            return None
        stored_at, value = hit
        if time.monotonic() - stored_at >= ttl_seconds:
            del _store[key]
            return None
        return value


def cache_set(key: str, value: Any) -> None:
    with _lock:
        _store[key] = (time.monotonic(), value)


def cache_age_seconds(key: str) -> float | None:
    with _lock:
        hit = _store.get(key)
        if hit is None:
            return None
        return time.monotonic() - hit[0]


def cache_clear() -> None:
    with _lock:
        _store.clear()
