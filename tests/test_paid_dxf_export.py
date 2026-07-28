"""Tests for the paid national DXF artifact builder."""

from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_paid_dxf_export.py"
SPEC = importlib.util.spec_from_file_location("build_paid_dxf_export", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sample_collection() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-57.6, -25.3]},
                "properties": {
                    "title": "Casa\nCentro",
                    "price_usd": 100000,
                    "area_ha": 0.05,
                    "city": "Asunción",
                },
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-57.5, -25.2]},
                "properties": {"source_id": "property-2"},
            },
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": []},
                "properties": {"title": "ignored"},
            },
        ],
    }


def test_point_features_filters_non_point_geometries() -> None:
    assert len(MODULE.point_features(sample_collection())) == 2


def test_build_dxf_emits_r12_points_and_metadata() -> None:
    result = MODULE.build_dxf(sample_collection())

    assert "AC1009" in result
    assert result.count("\nPOINT\n") == 2
    assert "Casa Centro" in result
    assert "USD 100,000" in result
    assert result.endswith("  0\nEOF\n")


def test_build_dxf_rejects_empty_input() -> None:
    try:
        MODULE.build_dxf({"type": "FeatureCollection", "features": []})
    except ValueError as error:
        assert str(error) == "input has no valid Point features"
    else:
        raise AssertionError("empty input must be rejected")
