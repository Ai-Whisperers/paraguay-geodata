"""Smoke tests for tools/national_tile_index.py.

Run:  python3 -m pytest tests/test_national_tile_index.py -v
or:   python3 tests/test_national_tile_index.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.national_tile_index import (  # noqa: E402
    PY_BBOX, TILE_KM, iterate_tiles, find_tile_id_at, priority_tile_ids,
)


def test_bbox_covers_all_known_anchors():
    """Every priority city must be inside PY_BBOX."""
    bbox = PY_BBOX
    from tools.national_tile_index import PRIORITY_CITIES
    for name, lat, lon in PRIORITY_CITIES:
        assert bbox["min_lon"] <= lon <= bbox["max_lon"], f"{name} lon {lon} outside bbox"
        assert bbox["min_lat"] <= lat <= bbox["max_lat"], f"{name} lat {lat} outside bbox"


def test_tile_count_in_expected_range():
    """Paraguay bbox at 10×10 km should yield ~7,000-8,500 tiles."""
    tiles = list(iterate_tiles())
    assert 7000 <= len(tiles) <= 8500, f"unexpected: {len(tiles)} tiles"


def test_tile_keys_are_unique():
    tiles = list(iterate_tiles())
    ids = [t["tile_id"] for t in tiles]
    assert len(set(ids)) == len(ids), "duplicate tile ids"


def test_find_tile_at_priority_cities():
    """Each PRIORITY_CITY lat/lon resolves to a valid tile_id."""
    from tools.national_tile_index import PRIORITY_CITIES
    tile_ids = {t["tile_id"] for t in iterate_tiles()}
    for name, lat, lon in PRIORITY_CITIES:
        tid = find_tile_id_at(lat, lon)
        assert tid in tile_ids, f"{name}: returned tile_id {tid} not in master"


def test_priority_tile_ids_all_in_master():
    """priority_tile_ids() returns only tile_ids that exist in the master grid."""
    master = {t["tile_id"] for t in iterate_tiles()}
    prio = set(priority_tile_ids())
    assert prio.issubset(master), f"priority has {prio - master} not in master"


def test_lqv_reference_tile_resolves():
    """LQV parcel (-25.5627515, -57.0355) lies within Paraguay bbox."""
    tid = find_tile_id_at(-25.5627515, -57.0355)
    assert tid.startswith("-57."), f"LQV tile id looks wrong: {tid}"


if __name__ == "__main__":
    test_bbox_covers_all_known_anchors()
    test_tile_count_in_expected_range()
    test_tile_keys_are_unique()
    test_find_tile_at_priority_cities()
    test_priority_tile_ids_all_in_master()
    test_lqv_reference_tile_resolves()
    print("All 6 tests passed.")
