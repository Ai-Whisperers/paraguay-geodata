"""Shared pytest fixtures for the Paraguay-Geodata test suite.

Provides:
- ``root_repo``    — absolute path to the repo root
- ``web_root``     — ``exports/web/`` (the deployable artifact)
- ``data_root``    — ``exports/web/data/``
- ``scripts_root`` — ``scripts/``
- ``tools_root``   — ``tools/``
- ``internal_data_root`` — ``data/`` (unpublished raw snapshots + tiles_seed)
- ``live_base_url`` — ``https://geodata.paragu-ai.com`` (overridable via env)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LIVE_BASE_URL = os.environ.get("PY_GEO_BASE_URL", "https://geodata.paragu-ai.com")
"""
Override the live base URL for live tests:
    PY_GEO_BASE_URL=https://staging.example.com pytest tests/
"""


@pytest.fixture(scope="session")
def root_repo() -> Path:
    """Absolute path to the repo root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def web_root() -> Path:
    """Path to ``exports/web/`` (the deployable artifact)."""
    return REPO_ROOT / "exports" / "web"


@pytest.fixture(scope="session")
def data_root() -> Path:
    """Path to ``exports/web/data/`` (publicly-served GeoJSON/JSON)."""
    return REPO_ROOT / "exports" / "web" / "data"


@pytest.fixture(scope="session")
def scripts_root() -> Path:
    """Path to ``scripts/`` (build pipelines, including hillshade)."""
    return REPO_ROOT / "scripts"


@pytest.fixture(scope="session")
def tools_root() -> Path:
    """Path to ``tools/`` (fetchers + rebuilds)."""
    return REPO_ROOT / "tools"


@pytest.fixture(scope="session")
def internal_data_root() -> Path:
    """Path to ``data/`` (unpublished snapshots, tile seeds)."""
    return REPO_ROOT / "data"


@pytest.fixture(scope="session")
def live_base_url() -> str:
    """Live base URL for endpoint-style tests. Override via PY_GEO_BASE_URL."""
    return LIVE_BASE_URL


@pytest.fixture
def live_only(request) -> None:
    """Marker: skip the test when ``PY_GEO_OFFLINE=1`` is set."""
    if os.environ.get("PY_GEO_OFFLINE") == "1":
        pytest.skip("live-only test (PY_GEO_OFFLINE=1)")
