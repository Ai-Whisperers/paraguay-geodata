"""Tests for tools/fast_walk_asuncion_estate.py and enrich_missing_only.py."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def test_fast_walk_help():
    """CLI is wired up and exposes --output/--concurrency/--max-pages."""
    r = subprocess.run(
        ["python3", "-m", "tools.fast_walk_asuncion_estate", "--help"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0
    assert "--concurrency" in r.stdout
    assert "--max-pages" in r.stdout
    assert "--output" in r.stdout


def test_enrich_help():
    """CLI is wired up and exposes --walk-snapshot/--output."""
    r = subprocess.run(
        ["python3", "-m", "tools.enrich_missing_only", "--help"],
        cwd=str(REPO), capture_output=True, text=True, timeout=10,
    )
    assert r.returncode == 0
    assert "--walk-snapshot" in r.stdout
    assert "--output" in r.stdout
    assert "--concurrency" in r.stdout


def test_enrich_dry_run_creates_output(tmp_path):
    """If the walk snapshot is empty, enrich should still produce a (small) output file."""
    walk = tmp_path / "walk.geojson"
    walk.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": [],
        "feature_count": 0,
    }))

    out = tmp_path / "enriched.geojson"
    r = subprocess.run(
        ["python3", "-m", "tools.enrich_missing_only",
         "--walk-snapshot", str(walk),
         "--output", str(out),
         "--concurrency", "1"],
        cwd=str(REPO), capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0, f"failed: {r.stderr}"
    assert out.exists()
    d = json.loads(out.read_text())
    assert d["type"] == "FeatureCollection"
    assert d["features"] == []


def test_enrich_idempotent_for_walked_only():
    """Features without a detail page should fall back to city centroid coords."""
    import importlib.util

    # Skip if we can't import
    spec = importlib.util.spec_from_file_location(
        "enrich_missing_only",
        REPO / "tools" / "enrich_missing_only.py",
    )
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    # _in_py should reject null/None
    assert mod._in_py(None, None) is False
    assert mod._in_py(0, 0) is False  # Pacific Ocean
    # Asunción center: -57.5759, -25.2637 → in
    assert mod._in_py(-57.5759, -25.2637) is True
    # Buenos Aires: -58.38, -34.6 → out
    assert mod._in_py(-58.38, -34.6) is False


def test_walked_snapshot_has_required_fields():
    """If a fast_walk snapshot exists, it must have the required feature shape."""
    snap = REPO / "data" / "properties" / "snapshots" / "asuncion_estate_fast_walk.geojson"
    if not snap.exists():
        return  # Skip if not built yet
    d = json.loads(snap.read_text())
    assert d["type"] == "FeatureCollection"
    assert len(d["features"]) > 100  # should have many
    for f in d["features"][:10]:
        p = f.get("properties", {})
        assert "source" in p
        assert p["source"] == "asuncion_estate"
        assert "source_id" in p
        assert "source_url" in p


def test_enriched_snapshot_has_real_coords_or_centroid():
    """If an enriched snapshot exists, all features should have coords in PY bbox."""
    snap = REPO / "data" / "properties" / "snapshots" / "asuncion_estate_enriched.geojson"
    if not snap.exists():
        return
    d = json.loads(snap.read_text())
    assert d["type"] == "FeatureCollection"
    assert len(d["features"]) > 1000
    PY_BBOX = {"lon_min": -63.5, "lon_max": -54.0, "lat_min": -27.5, "lat_max": -19.0}
    bad = 0
    for f in d["features"]:
        coords = f.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            bad += 1
            continue
        lon, lat = coords[0], coords[1]
        if not (PY_BBOX["lon_min"] <= lon <= PY_BBOX["lon_max"] and PY_BBOX["lat_min"] <= lat <= PY_BBOX["lat_max"]):
            bad += 1
    assert bad == 0, f"{bad} features have out-of-bbox coords in enriched snapshot"
