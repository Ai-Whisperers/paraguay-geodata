"""Tests for tools/build_deploy_meta.py — the single source of truth for "what's live?"."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "exports" / "web" / "data" / "deploy-meta.json"


def run():
    r = subprocess.run(
        ["python3", "-m", "tools.build_deploy_meta", "--deployer=test"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, f"build_deploy_meta failed: {r.stderr}"
    assert OUT.exists(), f"{OUT} not created"
    return json.loads(OUT.read_text())


def test_runs_clean():
    """Builder exits 0 and writes a valid JSON file."""
    meta = run()
    assert isinstance(meta, dict)
    assert "commit" in meta
    assert "deployed_at_utc" in meta
    assert "data_layers_loaded" in meta


def test_commit_is_current_head():
    """commit field matches `git rev-parse HEAD`."""
    meta = run()
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    ).stdout.strip()
    assert meta["commit"] == head, f"stale commit: {meta['commit']} vs {head}"


def test_deployed_at_recent():
    """deployed_at_utc is within the last 5 minutes."""
    from datetime import datetime, timezone
    meta = run()
    deployed = datetime.fromisoformat(meta["deployed_at_utc"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = (now - deployed).total_seconds()
    assert 0 <= delta < 300, f"deployed_at_utc is stale: {meta['deployed_at_utc']}"


def test_layers_counted():
    """data_layers_loaded is non-empty with feature counts."""
    meta = run()
    layers = meta["data_layers_loaded"]
    assert len(layers) >= 10, f"only {len(layers)} layers, expected ≥10"
    for layer in layers:
        assert "id" in layer
        assert "file" in layer
        if "features" in layer:
            assert layer["features"] >= 0


def test_total_features_reasonable():
    """live_features_total should be in the tens-of-thousands range."""
    meta = run()
    total = meta.get("live_features_total", 0)
    assert total > 10000, f"total too low: {total}"
    assert total < 100_000_000, f"total too high: {total}"


def test_deferred_handled():
    """Missing files land in deferred_sources, not data_layers_loaded."""
    meta = run()
    deferred = meta.get("deferred_sources", [])
    loaded_ids = {l["id"] for l in meta["data_layers_loaded"]}
    deferred_ids = {d["id"] for d in deferred}
    overlap = loaded_ids & deferred_ids
    assert not overlap, f"layer ids in both loaded and deferred: {overlap}"
