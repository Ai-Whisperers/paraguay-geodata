"""Smoke test for build_architect_export.py.

Verifies:
  • Script runs end-to-end without error.
  • Both bundles (national + Asunción) are valid GeoJSON FeatureCollections.
  • feature_counts reported in the envelope matches the actual features.
  • Every construction_zone feature has a Polygon geometry + ordinance metadata.
  • Every urban_zoning feature has a Polygon/MultiPolygon geometry.
  • The bundle is deterministic across runs (sorted features).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path("/root/paraguay-geodata")
WEB_DATA = REPO_ROOT / "exports" / "web" / "data"


def _run_builder() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/build_architect_export.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"builder crashed:\nstdout={result.stdout}\nstderr={result.stderr}"
    print("✓ builder ran successfully")


def test_builder_runs() -> None:
    _run_builder()


def _validate(path: Path, expected_total_min: int) -> dict:
    assert path.exists(), f"missing {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["type"] == "FeatureCollection"
    assert data["version"] == 1
    features = data["features"]
    assert len(features) >= expected_total_min, (
        f"too few features: {len(features)} < {expected_total_min}"
    )
    # feature_counts matches
    from collections import Counter
    actual = dict(Counter(f["properties"].get("layer_kind", "?") for f in features))
    actual["total"] = len(features)
    reported = data["feature_counts"]
    for k, v in actual.items():
        assert reported.get(k) == v, f"feature_counts mismatch for {k}: {reported.get(k)} != {v}"
    # Every feature has geometry
    no_geom = [f for f in features if not f.get("geometry") or not f["geometry"].get("type")]
    assert not no_geom, f"{len(no_geom)} features lack geometry"
    # Every construction_zone has a Polygon and ordinance_ref
    for f in features:
        if f["properties"].get("layer_kind") == "construction_zone":
            assert f["geometry"]["type"] == "Polygon"
            assert f["properties"].get("ordinance_ref")
            assert f["properties"].get("max_height_m") is not None
    # Every urban_zoning has a polygon (Polygon or MultiPolygon)
    for f in features:
        if f["properties"].get("layer_kind") == "urban_zoning":
            assert f["geometry"]["type"] in ("Polygon", "MultiPolygon")
    print(f"✓ {path.name} valid: {len(features)} features, counts={reported}")
    return data


def test_full_bundle_valid() -> None:
    _validate(WEB_DATA / "architect_export.geojson", expected_total_min=400)


def test_asuncion_bundle_valid() -> None:
    _validate(WEB_DATA / "architect_export_asuncion.geojson", expected_total_min=30)


def test_bundle_is_deterministic() -> None:
    """Run the builder twice and confirm the FEATURES (sans timestamp) are identical."""
    a = json.loads((WEB_DATA / "architect_export.geojson").read_text(encoding="utf-8"))
    _run_builder()
    b = json.loads((WEB_DATA / "architect_export.geojson").read_text(encoding="utf-8"))
    # Strip generated_at (timestamp) — features themselves must be deterministic.
    a.pop("generated_at", None)
    b.pop("generated_at", None)
    assert a == b, "bundle output is non-deterministic across runs"
    print("✓ bundle output is deterministic across runs (features stable)")


def main() -> int:
    _run_builder()
    _validate(WEB_DATA / "architect_export.geojson", expected_total_min=400)
    _validate(WEB_DATA / "architect_export_asuncion.geojson", expected_total_min=30)
    test_bundle_is_deterministic()
    print("\n✓ ALL SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
