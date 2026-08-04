"""Tests for tools/add_listing_numbers.py — assign stable listing numbers."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def test_help():
    r = subprocess.run(
        ["python3", "-m", "tools.add_listing_numbers", "--help"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0
    assert "--dry-run" in r.stdout


def test_dry_run_no_write():
    """--dry-run does not modify canonical_properties.geojson."""
    before = hashlib.sha256(
        (REPO / "data/properties/canonical_properties.geojson").read_bytes()
    ).hexdigest()
    r = subprocess.run(
        ["python3", "-m", "tools.add_listing_numbers", "--dry-run"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    after = hashlib.sha256(
        (REPO / "data/properties/canonical_properties.geojson").read_bytes()
    ).hexdigest()
    assert before == after


def test_after_run_every_listing_has_number():
    """After running, every listing has listing_number set to a unique int."""
    data = json.loads((REPO / "data/properties/canonical_properties.geojson").read_text())
    seen = set()
    for f in data["features"]:
        ln = f["properties"].get("listing_number")
        assert ln is not None, f"listing without number: {f['properties'].get('id')}"
        assert isinstance(ln, int), f"non-int listing_number: {ln}"
        assert ln >= 1
        assert ln not in seen, f"duplicate listing_number: {ln}"
        seen.add(ln)
    # Should cover exactly n listings with numbers 1..n
    assert seen == set(range(1, len(data["features"]) + 1)), "not a contiguous 1..n range"


def test_listing_numbers_stable_across_runs():
    """The same listing keeps the same number across two runs.

    We re-run twice and compare — if the IDs are still present and the
    assignment is deterministic, the numbers should match.
    """
    r1 = subprocess.run(
        ["python3", "-m", "tools.add_listing_numbers"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r1.returncode == 0
    data1 = json.loads((REPO / "data/properties/canonical_properties.geojson").read_text())
    by_id1 = {f["properties"]["id"]: f["properties"]["listing_number"] for f in data1["features"]}
    # Run again
    r2 = subprocess.run(
        ["python3", "-m", "tools.add_listing_numbers"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    assert r2.returncode == 0
    data2 = json.loads((REPO / "data/properties/canonical_properties.geojson").read_text())
    by_id2 = {f["properties"]["id"]: f["properties"]["listing_number"] for f in data2["features"]}
    # All keys should match
    assert by_id1.keys() == by_id2.keys()
    for k in by_id1:
        assert by_id1[k] == by_id2[k], f"number changed for {k}: {by_id1[k]} → {by_id2[k]}"


def test_listing_numbers_start_at_1():
    """First listing gets #1."""
    data = json.loads((REPO / "data/properties/canonical_properties.geojson").read_text())
    first = min(f["properties"]["listing_number"] for f in data["features"])
    assert first == 1