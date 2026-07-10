#!/usr/bin/env python3
"""scripts/seed_priority_tile_metas.py — seed per-tile metadata for priority tiles.

Run once per Phase 0 launch + whenever the PRIORITY_CITIES list grows.
Output: data/tiles_seed/<tile_id>.json (tracked in git, ~30-50 files).
        These are templates that Phase 1's fetch_tile.py can copy when it
        lands data, vs creating metadata on the fly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.national_tile_index import (  # noqa: E402
    iterate_tiles, priority_tile_ids, PRIORITY_CITIES,
)

LAYERS = [
    "dem", "esri_hd_lod2", "esri_hd_lod3", "sentinel2", "osm_10km",
    "mapbiomas", "hansen", "jrc_gsw", "hydrosheds", "firms", "gbif",
    "cerros", "streams", "properties", "price_surface",
]


def main() -> int:
    out_dir = REPO_ROOT / "data" / "tiles_seed"
    out_dir.mkdir(parents=True, exist_ok=True)
    prio = set(priority_tile_ids())
    prio_centroids = {
        t["tile_id"]: t for t in iterate_tiles() if t["tile_id"] in prio
    }
    written = 0
    for tile_id, tile in sorted(prio_centroids.items()):
        path = out_dir / f"{tile_id}.json"
        if not path.exists():
            path.write_text(json.dumps({
                "tile_id": tile["tile_id"],
                "centroid": tile["centroid"],
                "bbox_wsen": tile["bbox_wsen"],
                "utm_zone_hint": tile["utm_zone_hint"],
                "priority": True,
                "data_state": {l: False for l in LAYERS},
            }, indent=2))
            written += 1
    print(f"Seeded {len(prio_centroids)} priority tile metadata stubs "
          f"({written} new, {len(prio_centroids) - written} pre-existing).")
    print(f"Out dir: {out_dir}")
    print(f"Anchor cities covered: {len(PRIORITY_CITIES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
