"""tools/_mbtiles_to_pmtiles.py

Convert an MBTiles file (from tippecanoe) to a PMTiles single-file archive,
using the pmtiles Python lib directly.

PMTiles v3 spec differs from MBTiles on one thing: PMTiles uses a Hilbert
curve for tile id (Z+X+Y), while MBTiles uses TMS row numbers in SQLite.
We translate: PMTiles row = (1 << Z) - 1 - MBTiles_row.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

import pmtiles.tile as pt  # type: ignore
import pmtiles.writer as pw  # type: ignore


def _header_from_meta(meta: dict, *, zoom_min: int, zoom_max: int, n_tiles: int):
    """Build a PMTiles v3 header dict (pmtiles 3.7 takes a dict, not a class)."""
    bounds = [-180.0, -85.0511, 180.0, 85.0511]
    if "bounds" in meta:
        try:
            bounds = [float(x) for x in meta["bounds"].split(",")]
        except (ValueError, AttributeError):
            pass
    center = [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2, zoom_min]
    if "center" in meta:
        try:
            c = [float(x) for x in meta["center"].split(",")]
            center = c[:3]
        except (ValueError, AttributeError, IndexError):
            pass
    return {
        "spec_version": 3,
        "addressed_tiles_count": n_tiles,
        "tile_entries_count": n_tiles,
        "tile_contents_count": n_tiles,
        "clustered": True,
        "internal_compression": pt.Compression.GZIP,
        "tile_compression": pt.Compression.GZIP,
        "tile_type": pt.TileType.MVT,
        "min_zoom": zoom_min, "max_zoom": zoom_max,
        "min_lon_e7": int(bounds[0] * 1e7),
        "min_lat_e7": int(bounds[1] * 1e7),
        "max_lon_e7": int(bounds[2] * 1e7),
        "max_lat_e7": int(bounds[3] * 1e7),
        "center_lon_e7": int(center[0] * 1e7),
        "center_lat_e7": int(center[1] * 1e7),
        "center_zoom": int(center[2]),
    }


def convert(mbtiles_path: Path, pmtiles_path: Path) -> int:
    """Convert MBTiles → PMTiles."""
    if not mbtiles_path.exists():
        print(f"  ERROR: {mbtiles_path} does not exist")
        return 1
    print(f"  loading {mbtiles_path} ({mbtiles_path.stat().st_size:,} bytes)...")
    conn = sqlite3.connect(str(mbtiles_path))
    cur = conn.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles")
    rows = cur.fetchall()
    print(f"  {len(rows):,} tiles")

    if not rows:
        print("  ERROR: MBTiles has no tiles")
        return 1

    zoom_min = min(r[0] for r in rows)
    zoom_max = max(r[0] for r in rows)
    print(f"  zoom range: {zoom_min}-{zoom_max}")

    cur = conn.execute("SELECT name, value FROM metadata")
    meta = {k: v for k, v in cur.fetchall()}

    md_obj = {
        "name": "properties",
        "format": "pbf",
        "minzoom": zoom_min,
        "maxzoom": zoom_max,
        "bounds": meta.get("bounds", ""),
        "center": meta.get("center", ""),
        "attribution": "<a href='https://github.com/Ai-Whisperers/paraguay-geodata'>Ai-Whisperers</a> · CC0",
    }
    
    print(f"  writing {pmtiles_path}...")
    with pmtiles_path.open("wb") as f:
        writer = pw.Writer(f)
        for z, x, y, blob in rows:
            # MBTiles row 0 is bottom-left (TMS).  PMTiles uses XYZ (top-left).
            tms_y = (1 << z) - 1 - y
            tile_id = pt.zxy_to_tileid(z, x, tms_y)
            writer.write_tile(tile_id, blob)
        header = _header_from_meta(meta, zoom_min=zoom_min,
                                zoom_max=zoom_max, n_tiles=len(rows))
        writer.finalize(header, md_obj)
    conn.close()

    sz = pmtiles_path.stat().st_size
    print(f"  OK: {pmtiles_path} ({sz:,} bytes)")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to input .mbtiles")
    parser.add_argument("--output", required=True, help="Path to output .pmtiles")
    args = parser.parse_args(argv)
    return convert(Path(args.input), Path(args.output))


if __name__ == "__main__":
    sys.exit(main())
