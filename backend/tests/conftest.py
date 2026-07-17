"""Shared fixtures. Force the seed-backed repository so tests are hermetic."""
from __future__ import annotations

import os

import pytest

# Ensure no accidental Gemini calls and a fast Postgres refusal -> seed fallback.
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("POSTGRES_HOST", "127.0.0.1")
os.environ.setdefault("POSTGRES_PORT", "1")  # unreachable -> seed fallback

from helm.core.config import get_settings  # noqa: E402
from helm.persistence import Repository  # noqa: E402


@pytest.fixture
def repo() -> Repository:
    return Repository(get_settings())


@pytest.fixture
def seed_data(repo: Repository):
    return repo.service_areas(), repo.metric_series(), repo.budget_lines()
