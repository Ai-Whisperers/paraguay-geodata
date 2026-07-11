#!/usr/bin/env python3
"""scripts/export_priority_tiles.py — generate priority_tiles.json for the viewer.

Run:  python3 scripts/export_priority_tiles.py
Output: exports/web/data/priority_tiles.json (Pages-deployable, <25 MiB)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.national_tile_index import priority_tile_ids, iterate_tiles  # noqa: E402

prio = set(priority_tile_ids())
priority_tiles = [t for t in iterate_tiles() if t["tile_id"] in prio]
print(f"priority_tiles count: {len(priority_tiles)}")
out = {
    "version": "0.1.0",
    "description": "Priority 10x10 km tiles in Paraguay at urban anchor cities (Phase 1 coverage target).",
    "tile_count": len(priority_tiles),
    "tiles": priority_tiles,
}
out_path = REPO_ROOT / "exports" / "web" / "data" / "priority_tiles.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2))
sz = os.path.getsize(out_path)
print(f"priority_tiles.json size: {sz} bytes ({sz/1024:.1f} KB)")
print(f"first 3 tile_ids: {[t['tile_id'] for t in priority_tiles[:3]]}")