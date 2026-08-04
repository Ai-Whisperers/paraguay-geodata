"""Tests for tools/fetch_bcp_rates.py — BCP USD/PYG rate fetcher."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RATE_PATH = REPO / "data" / "properties" / "bcp_rates.json"


def test_help():
    """CLI is wired up."""
    r = subprocess.run(
        ["python3", "-m", "tools.fetch_bcp_rates", "--help"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0
    assert "--fallback" in r.stdout
    assert "--api-url" in r.stdout


def test_stub_writes_bcp_rates():
    """Without an API url, stub fallback writes a valid bcp_rates.json."""
    r = subprocess.run(
        ["python3", "-m", "tools.fetch_bcp_rates"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    assert RATE_PATH.exists()
    data = json.loads(RATE_PATH.read_text())
    assert "pyg_per_usd" in data
    assert "as_of_utc" in data
    assert "source" in data
    assert data["pyg_per_usd"] > 0


def test_stub_source_marker():
    """Stub fallback sets source='stub' so callers know they're on a placeholder."""
    data = json.loads(RATE_PATH.read_text())
    assert data["source"] == "stub"


def test_history_appended():
    """Running twice appends to the history array."""
    import json
    before = json.loads(RATE_PATH.read_text())
    n_before = len(before.get("history", []))
    subprocess.run(
        ["python3", "-m", "tools.fetch_bcp_rates"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    after = json.loads(RATE_PATH.read_text())
    assert len(after.get("history", [])) > n_before


def test_30d_average_recomputed():
    """30d avg is recomputed from history."""
    data = json.loads(RATE_PATH.read_text())
    assert "pyg_per_usd_30d_avg" in data
    assert "pyg_per_usd_30d_std" in data


def test_fallback_rate_is_used():
    """--fallback overrides the default stub rate."""
    r = subprocess.run(
        ["python3", "-m", "tools.fetch_bcp_rates", "--fallback", "8000"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    data = json.loads(RATE_PATH.read_text())
    assert data["pyg_per_usd"] == 8000
