"""
tools/fetch_tile.py — Per-tile data orchestrator.

Given a tile_id (or lat/lon), pull every data layer for that tile:
  DEM (Copernicus GLO-30) + derived (streams, cerros, contours, slope, aspect)
  Esri HD (z=17 LOD2 + z=18 LOD3)
  Sentinel-2 (RGB + NDVI + cloud mask)
  OSM 10 km (buildings, roads, water, waterways, landuse, places, pois, trees)
  MapBiomas Paraguay (land cover 2023)
  Hansen GFC (loss + gain)
  JRC Global Surface Water (waterbodies)
  HydroSHEDS (flow accumulation)
  FIRMS (last 7 days fire hotspots within tile bbox)
  GBIF (species observations within tile bbox)
  Property listings (active snapshot filtered to tile bbox)
  Price surface (clipped kriging output)

Heavy rasters go to data/tiles/<tile_id>/ (gitignored) and exports/big_data_excluded_from_deploy/.
Small GeoJSONs and PNG previews go to exports/web/data/tiles/<tile_id>/ (Pages-deployable).

Currently a STUB. Phase 1 fills in each fetch_* layer.

Run:
    python3 -m tools.fetch_tile '--tile-id=-57.069_-25.595'     # LQV reference (note the =)
    python3 -m tools.fetch_tile --lat -25.5627515 --lon -57.0355
    python3 -m tools.fetch_tile --all-priority                  # all 153 priority tiles
    python3 -m tools.fetch_tile --apply --skip-existing         # re-build even if data_state is true

NOTE: argparse treats values starting with `-` as flags. Quote the tile id with
`=` or pass `--tile-id=-...` to avoid the problem. The lat/lon form has no issue.

Class-level technique: see
  ~/.hermes/skills/devops/satellite-to-blender-pipeline/SKILL.md
  ~/.hermes/skills/lqv-bundle/SKILL.md
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.national_tile_index import (  # noqa: E402
    iterate_tiles,
    find_tile_id_at,
    priority_tile_ids,
    TILE_KM,
)


LAYERS = [
    "dem", "dem_derived_streams", "dem_derived_cerros", "dem_derived_contours",
    "dem_derived_slope_aspect",
    "esri_hd_lod2", "esri_hd_lod3",
    "sentinel2", "sentinel2_ndvi", "sentinel2_cloudmask",
    "osm_buildings", "osm_roads", "osm_water", "osm_waterways", "osm_landuse",
    "osm_places", "osm_pois", "osm_trees",
    "mapbiomas", "hansen_loss", "hansen_gain",
    "jrc_waterbodies", "hydrosheds", "firms", "gbif",
    "properties", "price_surface",
]


def fetch_one_layer(tile: dict, layer: str, force: bool = False) -> bool:
    """Stub — Phase 1 implements each layer.

    Returns True if the layer was built (or already exists), False on skip.
    """
    metadata_path = REPO_ROOT / "data" / "tiles" / tile["tile_id"] / "metadata.json"
    if not metadata_path.exists():
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(
            {"tile_id": tile["tile_id"], "centroid": tile["centroid"],
             "bbox_wsen": tile["bbox_wsen"], "utm_zone_hint": tile["utm_zone_hint"],
             "data_state": {l: False for l in LAYERS}},
            indent=2))
    meta = json.loads(metadata_path.read_text())
    if meta["data_state"].get(layer) and not force:
        return True  # already built, skip

    # TODO(Phase 1): dispatch to fetch_<layer>.py
    #   fetch_dem(tile) → data/tiles/<id>/dem/cop30_clipped.tif + derived streams/cerros/contours
    #   fetch_esri_hd(tile, z=17 or z=18) → data/tiles/<id>/esri/hd_lodN_zN.png
    #   fetch_sentinel2(tile) → data/tiles/<id>/sentinel2/{rgb,ndvi,scl}.tif
    #   fetch_osm(tile) → data/tiles/<id>/osm/*.geojson
    #   fetch_mapbiomas(tile) → data/tiles/<id>/mapbiomas/landcover_2023.geojson
    #   fetch_hansen(tile) → data/tiles/<id>/hansen/{loss,gain}.geojson
    #   fetch_jrc(tile) → data/tiles/<id>/jrc/waterbodies.geojson
    #   fetch_hydrosheds(tile) → data/tiles/<id>/hydrosheds/flow_acc.tif
    #   fetch_firms(tile) → data/tiles/<id>/firms/last7d.csv
    #   fetch_gbif(tile) → data/tiles/<id>/gbif/species.csv
    #   fetch_properties(tile, bbox) → filtered from exports/web/data/properties_<date>.geojson
    #   clip_price_surface(tile) → data/tiles/<id>/price_surface_clipped.tif

    # Phase 0 stub: log the layer that *would* be fetched.
    print(f"  [{tile['tile_id']}] STUB: would fetch {layer}")
    return True


def run_tile(tile: dict, force: bool = False, dry_run: bool = True) -> dict:
    """Run every layer for one tile. Phase 0 stub: log + return counts."""
    started = datetime.now(timezone.utc).isoformat()
    result = {
        "tile_id": tile["tile_id"],
        "centroid": tile["centroid"],
        "started_at_utc": started,
        "layer_outcomes": {},
    }
    if dry_run:
        for layer in LAYERS:
            result["layer_outcomes"][layer] = "would_fetch"
    else:
        for layer in LAYERS:
            ok = fetch_one_layer(tile, layer, force=force)
            result["layer_outcomes"][layer] = "ok" if ok else "skipped"

    result["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Per-tile data fetcher (Phase 0 stub).")
    parser.add_argument("--tile-id", default=None, help="Specific tile id (e.g. -57.069_-25.595).")
    parser.add_argument("--lat", type=float, default=None, help="Centroid lat (resolved to tile).")
    parser.add_argument("--lon", type=float, default=None, help="Centroid lon (resolved to tile).")
    parser.add_argument("--all-priority", action="store_true", help="All 153 priority tiles.")
    parser.add_argument("--apply", action="store_true", help="Actually run fetches (Phase 1). Default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Re-build even if data_state is true.")
    args = parser.parse_args(argv)

    tiles: list[dict]
    if args.tile_id:
        # resolve from any point in the tile
        sw_lon, sw_lat = (float(p) for p in args.tile_id.split("_"))
        mid_lat = sw_lat + (TILE_KM / 2 / 110.574)
        mid_lon = sw_lon + (TILE_KM / 2 / (111.320 * math.cos(math.radians(mid_lat))))
        tiles = [{"tile_id": args.tile_id, "centroid": [mid_lon, mid_lat],
                  "bbox_wsen": (sw_lon, sw_lat, sw_lon + 0.09, sw_lat + 0.09),
                  "utm_zone_hint": int((mid_lon + 180) / 6) + 1, "area_km2": 100.0}]
    elif args.lat is not None and args.lon is not None:
        tile_id = find_tile_id_at(args.lat, args.lon)
        tiles = [t for t in iterate_tiles() if t["tile_id"] == tile_id]
    elif args.all_priority:
        ids = set(priority_tile_ids())
        tiles = [t for t in iterate_tiles() if t["tile_id"] in ids]
    else:
        print("ERROR: provide --tile-id, --lat/--lon, or --all-priority.", file=sys.stderr)
        return 1

    dry_run = not args.apply
    if dry_run:
        print(f"[fetch_tile] DRY-RUN (Phase 0 stub) — {len(tiles)} tile(s), {len(LAYERS)} layers each")
    else:
        print(f"[fetch_tile] APPLY — {len(tiles)} tile(s), {len(LAYERS)} layers each")

    overall_started = time.time()
    summaries = []
    for i, tile in enumerate(tiles, 1):
        t0 = time.time()
        result = run_tile(tile, force=args.force, dry_run=dry_run)
        print(f"  [{i}/{len(tiles)}] {tile['tile_id']}  centre={result['centroid']}  "
              f"({time.time() - t0:.2f}s)")
        summaries.append(result)
    print(f"\nTotal: {time.time() - overall_started:.2f}s for {len(tiles)} tile(s)")
    if not dry_run:
        out = REPO_ROOT / "exports" / "web" / "data" / "tile_fetch_summary.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"ran_at_utc": datetime.now(timezone.utc).isoformat(),
                                   "tile_count": len(tiles), "layer_count": len(LAYERS),
                                   "summaries": summaries}, indent=2))
        print(f"Summary written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
