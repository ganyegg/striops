"""Filesystem path resolution for datasets (seed + live cache)."""
from __future__ import annotations

import os
from pathlib import Path


def datasets_dir() -> Path:
    """Locate the datasets/ directory across docker and local-dev layouts."""
    candidates = []
    env = os.environ.get("HELM_DATASETS_DIR")
    if env:
        candidates.append(Path(env))
    here = Path(__file__).resolve()
    # backend/helm/core/paths.py -> repo root is parents[3]
    candidates.append(here.parents[3] / "datasets")
    candidates.append(Path.cwd() / "datasets")
    candidates.append(Path.cwd().parent / "datasets")
    for c in candidates:
        if c.exists():
            return c
    # Default to repo-root guess even if missing; callers handle absence.
    return here.parents[3] / "datasets"


def seed_dir() -> Path:
    return datasets_dir() / "seed"


def cache_dir() -> Path:
    d = datasets_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d
