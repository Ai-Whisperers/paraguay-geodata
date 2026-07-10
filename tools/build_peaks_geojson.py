"""
tools/build_peaks_geojson.py — Extract cerros/summits from a per-tile DEM.

Algorithm: closed contour rings + multi-contour test (≥2 elevation levels
at decreasing area = true peak, not saddle).

Class-level technique: see
  ~/.hermes/skills/devops/satellite-to-blender-pipeline/references/dem-derived-cerros-peak-detection.md
  (the canonical reference; this script implements it for the national-scale
  tile fabric in /data/tiles/<id>/dem/.)

Run:
    python3 -m tools.build_peaks_geojson --tile-id -57.069_-25.595
    python3 -m tools.build_peaks_geojson --all-priority

Inputs:
    data/tiles/<tile_id>/dem/cop30_clipped.tif

Outputs:
    data/tiles/<tile_id>/cerros.geojson   (full precision, internal use)
    exports/web/data/tiles/<tile_id>/cerros.geojson   (≤ 25 MiB, public)

TODO(Phase 1): implement. Template lives at:
  /root/la-quebrada-viva/tools/build_peaks_geojson.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def build_peaks(tile_id: str) -> int:
    """Returns count of cerros detected. Implementation deferred to Phase 1."""
    print(f"  [build_peaks] STUB for {tile_id} — Phase 1 will implement")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build peaks/cerros GeoJSON from per-tile DEM (Phase 1 stub).")
    parser.add_argument("--tile-id", default=None, help="Specific tile id (e.g. -57.069_-25.595).")
    parser.add_argument("--all-priority", action="store_true", help="All 153 priority tiles.")
    args = parser.parse_args(argv)
    if not args.tile_id and not args.all_priority:
        print("ERROR: --tile-id or --all-priority required.", file=sys.stderr)
        return 1
    if args.tile_id:
        build_peaks(args.tile_id)
    else:
        from tools.national_tile_index import priority_tile_ids
        for tid in priority_tile_ids():
            build_peaks(tid)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
