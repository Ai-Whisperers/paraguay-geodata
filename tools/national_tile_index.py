"""
tools/national_tile_index.py — Paraguay national 10x10 km tile fabric index.

Produces /exports/web/data/tile_index.json + /data/tiles/<id>/metadata.json
for every tile in the Paraguay bbox at 10x10 km resolution.

Class-level technique: see umbrella skill
`~/.hermes/skills/devops/satellite-to-blender-pipeline/SKILL.md`
and project-instance skill `~/.hermes/skills/lqv-bundle/SKILL.md`
(the technique was validated on LQV at the 10x10 km scale in Paraguarí,
now we replicate it across all of Paraguay).

Run:
    python3 -m tools.national_tile_index           # writes tile_index.json + per-tile metadata
    python3 -m tools.national_tile_index --dry-run # prints summary, writes nothing
    python3 -m tools.national_tile_index --box 21JWL  # filter to one UTM 10x10 box
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Iterable, Iterator


# Paraguay bounding box (WGS84, lat/lon envelope)
# Source: Natural Earth simplified country polygon. Generous so Chaco ripio & Rio Apa tail included.
PY_BBOX = {
    "min_lon": -62.645,
    "min_lat": -27.585,
    "max_lon": -54.265,
    "max_lat": -19.275,
}

# 10x10 km tile size — proven at LQV scale
TILE_KM = 10.0


def _km_per_degree_lat() -> float:
    """1 degree latitude ≈ 110.574 km (constant)."""
    return 110.574


def _km_per_degree_lon(lat_deg: float) -> float:
    """Cos-corrected (latitude-aware)."""
    return 111.320 * math.cos(math.radians(lat_deg))


def tile_size_degrees(lat_center: float) -> tuple[float, float]:
    """Width/height in degrees for a TILE_KM x TILE_KM box at latitude lat_center."""
    dlat = TILE_KM / _km_per_degree_lat()
    dlon = TILE_KM / _km_per_degree_lon(lat_center)
    return dlon, dlat  # (delta_lon, delta_lat)


def iterate_tiles(
    bbox: dict = PY_BBOX,
    tile_km: float = TILE_KM,
) -> Iterator[dict]:
    """Yield every 10x10 km tile in the Paraguay bbox.

    Each tile is anchored to its SW corner. The tile id is `<lon>W_<lat>S`
    with both coords rounded to 3 decimal places (~110 m precision),
    e.g. `-57.123_-25.567`. Coordinates are clamped to bbox.
    """
    lat = bbox["min_lat"]
    while lat < bbox["max_lat"]:
        dlon, dlat = tile_size_degrees(lat + (tile_km / 2 / _km_per_degree_lat()))
        lon = bbox["min_lon"]
        while lon < bbox["max_lon"]:
            # Clamp tile to bbox — last row/col tiles may be partial.
            tile_max_lon = min(lon + dlon, bbox["max_lon"])
            tile_max_lat = min(lat + dlat, bbox["max_lat"])
            tile_id = f"{lon:.3f}_{lat:.3f}"
            centroid_lat = (lat + tile_max_lat) / 2
            centroid_lon = (lon + tile_max_lon) / 2
            yield {
                "tile_id": tile_id,
                "centroid": [centroid_lon, centroid_lat],
                "bbox": [lon, lat, tile_max_lon, tile_max_lat],  # GeoJSON order: [W, S, E, N]
                "bbox_wsen": (lon, lat, tile_max_lon, tile_max_lat),
                "utm_zone_hint": int(math.floor((centroid_lon + 180) / 6) + 1),
                "area_km2": (tile_max_lon - lon) * (tile_max_lat - lat)
                            * _km_per_degree_lat() * _km_per_degree_lon(centroid_lat),
            }
            lon += dlon
        lat += dlat


def find_tile_id_at(lat: float, lon: float) -> str:
    """Return the tile_id that contains the given point. O(n) — use sparingly."""
    for tile in iterate_tiles():
        w, s, e, n = tile["bbox_wsen"]
        if w <= lon <= e and s <= lat <= n:
            return tile["tile_id"]
    raise ValueError(f"Point {lat},{lon} is outside Paraguay bbox")


# Urban + venta anchor cities — used as priority targets for Phase 1.
# These are the dense-population + high-listings-activity areas to build first.
PRIORITY_CITIES: list[tuple[str, float, float]] = [
    # (city, lat, lon) — Phase 1 will fetch the 9 tiles that contain/cross these centroids
    ("Asunción",                    -25.2637, -57.5759),
    ("Ciudad del Este",             -25.5097, -54.6111),
    ("San Lorenzo",                 -25.3396, -57.5089),
    ("Luque",                       -25.2699, -57.4925),
    ("Capiatá",                     -25.3556, -57.4178),
    ("Fernando de la Mora",         -25.3167, -57.6000),
    ("Lambaré",                     -25.3200, -57.6500),
    ("Encarnación",                 -27.3367, -55.8667),
    ("Pedro Juan Caballero",        -22.5446, -55.7258),
    ("Concepción",                  -23.4011, -57.4411),
    ("Villarrica",                  -25.7833, -56.4500),
    ("Coronel Oviedo",              -25.4167, -56.4000),
    ("Itauguá",                     -25.3833, -57.3500),
    ("Mariano Roque Alonso",        -25.1667, -57.5500),
    ("Presidente Franco",           -25.5333, -54.6167),
    ("Pilar",                       -26.8583, -58.2986),
    ("Caaguazú",                    -25.4833, -56.0167),
    ("Salto del Guairá",            -24.0667, -54.3500),
    ("San Juan Bautista",           -26.6667, -57.1500),
    ("Caazapá",                     -26.1500, -56.3833),
]


def priority_tile_ids(k_per_city: int = 9) -> list[str]:
    """Return the unique tile ids covering the centroid + k_per_city neighbours
    (a 3x3 box of 10 km tiles) around each priority city.

    3x3 = 90 km x 90 km — enough to cover metropolitan area + immediate venta belt.
    """
    ids: set[str] = set()
    for _city, lat, lon in PRIORITY_CITIES:
        # 3x3 means ±1 tile around the centroid tile
        center_id = find_tile_id_at(lat, lon)
        sw_lon = float(center_id.split("_")[0])
        sw_lat = float(center_id.split("_")[1])
        # Tile step sizes (degrees). dlat is constant (110.574 km/deg).
        # dlon depends on latitude (cos correction).
        dlat_deg = TILE_KM / _km_per_degree_lat()
        mid_lat = sw_lat + dlat_deg / 2
        dlon_deg = TILE_KM / _km_per_degree_lon(mid_lat)
        for dlat_step in (-1, 0, 1):
            for dlon_step in (-1, 0, 1):
                nbr_id = f"{sw_lon + dlon_step * dlon_deg:.3f}_{sw_lat + dlat_step * dlat_deg:.3f}"
                # Verify this is a real tile (some are out of bbox for border cities).
                if any(t["tile_id"] == nbr_id for t in iterate_tiles()):
                    ids.add(nbr_id)
    return sorted(ids)


def write_outputs(
    tiles: Iterable[dict],
    out_dir: Path = Path("exports/web/data"),
    tiles_dir: Path = Path("data/tiles"),
    dry_run: bool = False,
) -> dict:
    """Write the master tile_index.json + per-tile metadata directories.

    Returns a summary dict.
    """
    tiles = list(tiles)
    summary = {
        "tile_count": len(tiles),
        "bbox": PY_BBOX,
        "tile_km": TILE_KM,
        "utm_zones": sorted({t["utm_zone_hint"] for t in tiles}),
        "lqv_reference_tile": find_tile_id_at(-25.5627515, -57.0355),  # La Quebrada Viva
    }
    if dry_run:
        return summary

    out_dir.mkdir(parents=True, exist_ok=True)
    tiles_dir.mkdir(parents=True, exist_ok=True)

    # Master index (small, served from Pages)
    index_path = out_dir / "tile_index.json"
    index = {
        "version": "0.1.0",
        "generated_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "py_bbox": PY_BBOX,
        "tile_km": TILE_KM,
        "tiles": tiles,
        "summary": summary,
    }
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False))

    # Per-tile metadata dir — record what data SHOULD exist for this tile.
    # Actual data fetching happens in `tools/fetch_tile.py`.
    for t in tiles:
        meta_dir = tiles_dir / t["tile_id"]
        meta_dir.mkdir(parents=True, exist_ok=True)
        meta_path = meta_dir / "metadata.json"
        if not meta_path.exists():
            meta_path.write_text(json.dumps(
                {
                    "tile_id": t["tile_id"],
                    "centroid": t["centroid"],
                    "bbox_wsen": t["bbox_wsen"],
                    "utm_zone_hint": t["utm_zone_hint"],
                    "data_state": {
                        "dem": False,
                        "esri_hd_lod2": False,
                        "esri_hd_lod3": False,
                        "sentinel2": False,
                        "osm_10km": False,
                        "mapbiomas": False,
                        "hansen": False,
                        "jrc_gsw": False,
                        "hydrosheds": False,
                        "firms": False,
                        "gbif": False,
                        "cerros": False,
                        "streams": False,
                        "properties": False,
                        "price_surface": False,
                    },
                },
                indent=2,
            ))

    return summary


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Generate the Paraguay 10x10 km tile fabric index.")
    parser.add_argument("--dry-run", action="store_true", help="Print summary, write nothing.")
    parser.add_argument("--out", default="exports/web/data", help="Output dir for tile_index.json.")
    parser.add_argument("--tiles-dir", default="data/tiles", help="Per-tile metadata dir.")
    parser.add_argument("--box", default=None, help="(optional) filter to one tile by id (debug).")
    parser.add_argument("--report-only", action="store_true", help="Just print bbox stats.")
    args = parser.parse_args(argv)

    tiles_iter = iterate_tiles()
    if args.box:
        tiles_iter = (t for t in iterate_tiles() if t["tile_id"].startswith(args.box))

    summary = write_outputs(
        tiles_iter,
        out_dir=Path(args.out),
        tiles_dir=Path(args.tiles_dir),
        dry_run=args.dry_run or args.report_only,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
