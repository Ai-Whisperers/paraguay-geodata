#!/usr/bin/env python3
"""scripts/geofabrik_admin_to_geojson.py — extract PY distritos + deptos from Geofabrik.

Reads gis_osm_adminareas_a_free_1.shp with geopandas, filters admin_level=6
(distritos = 262) and admin_level=4 (departamentos = 17), simplifies with Douglas-Peucker
for downstream deploy, writes to exports/web/data/admin/distritos.geojson + deptos.

Run:
    python3 scripts/geofabrik_admin_to_geojson.py <shp_dir> <output_dir>

e.g.:
    python3 scripts/geofabrik_admin_to_geojson.py /tmp/py_geofabrik exports/web/data/admin
"""
import sys
import json
import math
from pathlib import Path


def douglas_peucker(points, tol):
    """Iterative Douglas-Peucker simplification."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = True
    keep[-1] = True
    _dp(points, 0, len(points) - 1, tol, keep)
    return [p for p, k in zip(points, keep) if k]


def _dp(points, lo, hi, tol, keep):
    if hi <= lo + 1:
        return
    x0, y0 = points[lo]
    x1, y1 = points[hi]
    dmax = 0
    idx = lo
    dx = x1 - x0
    dy = y1 - y0
    norm = (dx * dx + dy * dy) ** 0.5 or 1
    for i in range(lo + 1, hi):
        x, y = points[i]
        # perpendicular distance from (x,y) to line through (x0,y0) and (x1,y1)
        num = abs(dy * x - dx * y + x1 * y0 - y1 * x0)
        d = num / norm
        if d > dmax:
            dmax = d
            idx = i
    if dmax > tol:
        keep[idx] = True
        _dp(points, lo, idx, tol, keep)
        _dp(points, idx, hi, tol, keep)


def simplify_ring(ring, tol):
    if len(ring) < 4:
        return ring
    closed = ring[0] == ring[-1]
    pts = ring[:-1] if closed else ring
    simp = douglas_peucker(pts, tol)
    if closed and simp and simp[0] != simp[-1]:
        simp.append(simp[0])
    return simp


def simplify_geom(geom, tol):
    t = geom.get("type")
    if t == "Polygon":
        # Standard Polygon coords: [ [ring, ring, ...] ] — single polygon with N rings.
        # But geopandas sometimes writes single-ring polys as [ [ring] ] (1 polygon, 1 ring),
        # which my old code interpreted as 1 polygon with 1 ring of N points; the for-loops
        # then mistakenly called simplify_ring(point, tol). Detect both.
        new_coords = []
        for entry in geom["coordinates"]:
            if not entry:
                continue
            # If first element is itself a [x,y], this entry is a RING (list of points),
            # so the polygon has only one ring.
            if isinstance(entry[0], (list, tuple)) and len(entry[0]) == 2 and isinstance(entry[0][0], (int, float)):
                new_coords.append(simplify_ring(entry, tol))
            else:
                # Multi-ring polygon: each element is a ring
                for ring in entry:
                    new_coords.append(simplify_ring(ring, tol))
        return {"type": "Polygon", "coordinates": new_coords} if new_coords else geom
    if t == "MultiPolygon":
        # [ [ [ring, ring, ...] ] ... ]
        new_coords = []
        for mp in geom["coordinates"]:
            new_mp = []
            for entry in mp:
                if isinstance(entry[0], (list, tuple)) and len(entry[0]) == 2 and isinstance(entry[0][0], (int, float)):
                    new_mp.append(simplify_ring(entry, tol))
                else:
                    for ring in entry:
                        new_mp.append(simplify_ring(ring, tol))
            new_coords.append(new_mp)
        return {"type": "MultiPolygon", "coordinates": new_coords}
    return geom


def main() -> int:
    shp_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0005
    out_dir.mkdir(parents=True, exist_ok=True)

    import geopandas as gpd
    shp = shp_dir / "gis_osm_adminareas_a_free_1.shp"
    print(f"Reading {shp}...")
    gdf = gpd.read_file(shp)
    print(f"Total features: {len(gdf)}")
    print(f"Columns: {list(gdf.columns)}")
    print(f"fclass value counts (admin levels):")
    print(gdf["fclass"].value_counts())

    LEVELS = {
        "admin_level3": ("national", None),
        "admin_level4": ("deptos", 4),
        "admin_level6": ("distritos", 6),
        "admin_level7": ("distritos_sub", 7),
        "admin_level8": ("localidades", 8),
        "admin_level9": ("barrios_py", 9),
        "admin_level10": ("barrios_int", 10),
        "admin_level11": ("barrios_sub", 11),
    }

    for fclass, (label, admin_num) in LEVELS.items():
        sub = gdf[gdf["fclass"] == fclass]
        if len(sub) == 0:
            continue
        if fclass == "admin_level3":  # Skip the national-level polygon
            continue
        print(f"\nfclass={fclass} → {len(sub)} features ({label})")
        if sub.crs is None:
            sub = sub.set_crs("EPSG:4326")
        else:
            sub = sub.to_crs("EPSG:4326")
        sub = sub[["osm_id", "name", "code", "geometry"]].copy()
        gj = json.loads(sub.to_json())
        features = []
        for f in gj["features"]:
            props = f["properties"]
            new_props = {k: v for k, v in props.items() if k != "geometry" and v is not None}
            new_props["source"] = "OSM via Geofabrik"
            new_props["admin_level"] = admin_num
            new_props["layer"] = label
            f["properties"] = new_props
            if f.get("geometry"):
                f["geometry"] = simplify_geom(f["geometry"], tol)
            features.append(f)

        out_path = out_dir / f"{label}.geojson"
        out_path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
        size = out_path.stat().st_size
        print(f"  wrote {out_path} — {len(features)} features, {size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())