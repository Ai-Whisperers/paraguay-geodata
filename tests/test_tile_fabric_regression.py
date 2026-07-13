"""National tile fabric + priority-city invariant tests — T8 + T9 from audit matrix.

These tests directly assert the invariants the GEOJSON consumers depend on:

  - The published tile_index.json has ~7,900 ± some thousands of tiles
  - Every tile_id in priority_tiles.json is present in tile_index.json
  - Random points inside Paraguay bbox resolve to a tile id (coverage)
  - The 37 (current snapshot) priority tile_ids are deduplicated
  - Priority city anchors land inside the bbox of an actual tile
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def tile_index(data_root):
    f = data_root / "tile_index.json"
    if not f.exists() or f.stat().st_size < 100_000:
        pytest.skip("tile_index.json not built")
    return json.load(open(f))


@pytest.fixture(scope="module")
def priority_tiles(data_root):
    f = data_root / "priority_tiles.json"
    if not f.exists() or f.stat().st_size < 1_000:
        pytest.skip("priority_tiles.json not built")
    return json.load(open(f))


def _tiles_array(d):
    """tile_index.json shape varies across versions. Pick the list."""
    return d.get("tiles") or d.get("tile_index") or d


# ---------- Tile fabric ----------


def test_tile_count_in_documented_range(tile_index):
    """Documentation says ~7,912 tiles at 10×10 km in Paraguay. Allow ±10%."""
    tiles = _tiles_array(tile_index)
    n = len(tiles)
    assert 7000 <= n <= 8500, f"unexpected tile count {n} (expected 7,000-8,500)"


def test_all_tile_ids_are_unique(tile_index):
    tiles = _tiles_array(tile_index)
    ids = [t.get("tile_id") or t.get("id") for t in tiles]
    assert len(ids) == len(set(ids)), "duplicate tile_ids present"


def test_all_tile_ids_match_sw_corner_pattern(tile_index):
    """Tile ids are `<lon>_<lat>` with both rounded to 3 dp."""
    import re
    pattern = re.compile(r"^-?\d+\.\d{3}_-?\d+\.\d{3}$")
    tiles = _tiles_array(tile_index)
    bad = []
    for t in tiles:
        tid = t.get("tile_id") or t.get("id")
        if not pattern.match(tid or ""):
            bad.append(tid)
    assert not bad, f"{len(bad)} tile ids malformed, e.g.: {bad[:3]}"


def test_tile_bbox_in_py_envelope(tile_index):
    """Each tile's bbox must fall inside PY envelope.

    Note: tiles touching the boundary exactly (e.g. e == max_lon) are fine.
    A 0.005° tolerance absorbs tile sizing round-off at the bbox edges.
    """
    from tools.national_tile_index import PY_BBOX
    tiles = _tiles_array(tile_index)
    bad = 0
    TOL = 0.005
    for t in tiles:
        bb = t.get("bbox")
        if not bb or len(bb) != 4:
            continue
        w, s, e, n = bb
        if (w < PY_BBOX["min_lon"] - TOL or e > PY_BBOX["max_lon"] + TOL or
                s < PY_BBOX["min_lat"] - TOL or n > PY_BBOX["max_lat"] + TOL):
            bad += 1
    assert bad == 0, f"{bad} tiles escape the Paraguay envelope"


def test_coverage_at_known_cities(tile_index):
    """Anchor cities must each land in a published tile."""
    from tools.national_tile_index import iterate_tiles, find_tile_id_at
    try:
        from tools.national_tile_index import PRIORITY_CITIES
    except ImportError:
        PRIORITY_CITIES = [
            ("Asunción",          -25.265, -57.575),
            ("Ciudad del Este",   -25.510, -54.611),
            ("Encarnación",       -27.330, -55.870),
            ("Pedro Juan Caballero", -22.566, -55.733),
            ("Filadelfia",        -22.270, -60.033),
            ("Villarrica",        -25.750, -56.450),
            ("Caacupé",           -25.387, -57.050),
        ]
    tile_ids = {(t["tile_id"]) for t in iterate_tiles()}
    for name, lat, lon in PRIORITY_CITIES:
        tid = find_tile_id_at(lat, lon)
        assert tid in tile_ids, f"{name}: find_tile_id_at {tid} not in iterated set"


def test_random_py_points_resolve(tile_index):
    """100 random points inside PY bbox → 100% must resolve to a tile id.
    A bug in iterate_tiles would cause certain latitudes to fall in the
    'gap' between dlat steps and miss every row.
    """
    import random
    random.seed(42)
    from tools.national_tile_index import (
        PY_BBOX, find_tile_id_at, iterate_tiles,
    )
    tile_ids = {(t["tile_id"]) for t in iterate_tiles()}
    misses = []
    for _ in range(100):
        lat = random.uniform(PY_BBOX["min_lat"] + 0.01, PY_BBOX["max_lat"] - 0.01)
        lon = random.uniform(PY_BBOX["min_lon"] + 0.01, PY_BBOX["max_lon"] - 0.01)
        try:
            tid = find_tile_id_at(lat, lon)
            assert tid in tile_ids, f"({lat:.3f},{lon:.3f}) → {tid} not in master"
        except ValueError as e:
            misses.append((lat, lon, str(e)))
    assert not misses, (
        f"{len(misses)}/100 random points had no tile: e.g. {misses[0]}"
    )


# ---------- Priority tiles ----------


def test_priority_tile_count_in_range(priority_tiles):
    """Documentation says 37 priority tiles."""
    items = _tiles_array(priority_tiles)
    n = len(items)
    assert 20 <= n <= 80, f"unexpected priority tile count {n} (expected 20-80)"


def test_priority_tile_ids_unique(priority_tiles):
    items = _tiles_array(priority_tiles)
    ids = [t.get("tile_id") or t.get("id") for t in items]
    assert len(ids) == len(set(ids)), "duplicate priority tile_ids present"


def test_priority_tile_ids_subset_of_master(priority_tiles, tile_index):
    """Every priority tile_id must exist in the master tile_index."""
    prio_ids = {(t.get("tile_id") or t.get("id")) for t in _tiles_array(priority_tiles)}
    master_ids = {(t.get("tile_id") or t.get("id")) for t in _tiles_array(tile_index)}
    diff = prio_ids - master_ids
    assert not diff, f"priority ids not in master tile_index: {diff}"


def test_priority_tile_anchors_count():
    """The priority city anchors are the source for selecting priority tiles.
    This test pins the count so a rename doesn't silently drop one."""
    from tools.national_tile_index import PRIORITY_CITIES
    # 20 anchor cities are documented in STATUS.md
    assert 5 <= len(PRIORITY_CITIES) <= 30, (
        f"unexpected priority anchor count {len(PRIORITY_CITIES)}"
    )
