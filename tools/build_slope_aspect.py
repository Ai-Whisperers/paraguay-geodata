"""
tools/build_slope_aspect.py — Slope / aspect / hillshade from per-tile DEM.

Class-level technique: see
  ~/.hermes/skills/devops/satellite-to-blender-pipeline/references/dem-derived-cerros-peak-detection.md

Run:
    python3 -m tools.build_slope_aspect --tile-id -57.069_-25.595

Inputs:
    data/tiles/<tile_id>/dem/cop30_clipped.tif

Outputs (Pages-deployable):
    exports/web/data/tiles/<tile_id>/slope.png
    exports/web/data/tiles/<tile_id>/aspect.png
    exports/web/data/tiles/<tile_id>/hillshade.png
    exports/web/data/tiles/<tile_id>/hillshade_multi.png   (multi-azimuth blend)

TODO(Phase 1): implement. Template lives at:
  /root/la-quebrada-viva/tools/build_slope_aspect.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def build_slope_aspect(tile_id: str) -> None:
    print(f"  [build_slope_aspect] STUB for {tile_id} — Phase 1 will implement")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build slope/aspect/hillshade from per-tile DEM (Phase 1 stub).")
    parser.add_argument("--tile-id", default=None)
    parser.add_argument("--all-priority", action="store_true")
    args = parser.parse_args(argv)
    if not args.tile_id and not args.all_priority:
        print("ERROR: --tile-id or --all-priority required.", file=sys.stderr)
        return 1
    if args.tile_id:
        build_slope_aspect(args.tile_id)
    else:
        from tools.national_tile_index import priority_tile_ids
        for tid in priority_tile_ids():
            build_slope_aspect(tid)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
