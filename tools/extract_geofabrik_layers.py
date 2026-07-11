#!/usr/bin/env python3
"""tools/extract_geofabrik_layers.py

Convert Geofabrik Paraguay shapefiles to GeoJSON layers ready for our viewer.

Reads (after you've unzipped `paraguay-latest-free.shp.zip`):
  - gis_osm_roads_free_1.shp        → roads.geojson (LineString)
  - gis_osm_buildings_a_free_1.shp → buildings.geojson (Polygon/MultiPolygon)
  - gis_osm_water_a_free_1.shp      → water.geojson (Polygon)
  - gis_osm_natural_a_free_1.shp    → natural.geojson (Polygon)
  - gis_osm_landuse_a_free_1.shp    → landuse.geojson (Polygon)
  - gis_osm_adminareas_a_free_1.shp → admin.geojson (already have via Geofabrik-pbf path)

Output to exports/web/data/ with size cap on individual layers.

Usage:
  python3 tools/extract_geofabrik_layers.py --src /tmp/geofabrik-paraguay
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import shapefile
except ImportError:
    print('pip install pyshp', file=sys.stderr)
    raise

ROOT = Path('/root/paraguay-geodata')
OUT_DIR = ROOT / 'exports/web/data'

# Map shp base name → output filename + geom type
LAYER_MAP = [
    ('gis_osm_roads_free_1', 'roads.geojson', 'LineString'),
    ('gis_osm_buildings_a_free_1', 'buildings.geojson', 'Polygon'),
    ('gis_osm_water_a_free_1', 'water.geojson', 'Polygon'),
    ('gis_osm_natural_a_free_1', 'natural.geojson', 'Polygon'),
    ('gis_osm_landuse_a_free_1', 'landuse.geojson', 'Polygon'),
    ('gis_osm_adminareas_a_free_1', 'geofabrik_admin.geojson', 'Polygon'),
]


def shp_to_features(src_dir: Path, base: str, geom_type: str, max_n: int) -> tuple[list, list]:
    """Return (features, field_names)."""
    shp_path = src_dir / f'{base}.shp'
    if not shp_path.exists():
        print(f'  [skip] {shp_path} not found')
        return [], []
    r = shapefile.Reader(str(shp_path))
    field_names = [f[0] for f in r.fields[1:]]  # skip DeletionFlag
    print(f'  {base}: {len(r)} records, fields={field_names[:8]}...')

    features = []
    skipped = 0
    empty = 0
    broken = 0
    i = 0
    while i < len(r):
        if len(features) >= max_n:
            print(f'  [cap] stopped at {max_n}')
            break
        try:
            sr = r.shapeRecord(i)
        except Exception as e:
            broken += 1
            i += 1
            continue
        i += 1
        rec = sr.record
        shape = sr.shape
        if shape is None or not getattr(shape, 'points', None):
            empty += 1
            continue
        # build properties
        props = {}
        for j, name in enumerate(field_names):
            try:
                v = rec[j]
            except Exception:
                continue
            if isinstance(v, bytes):
                try:
                    v = v.decode('utf-8', errors='replace')
                except Exception:
                    v = str(v)
            if isinstance(v, str) and len(v) > 200:
                v = v[:200]
            props[name] = v
        # build geometry
        pts = shape.points or []
        parts = shape.parts or [0]
        if geom_type == 'LineString' and len(pts) < 2:
            skipped += 1
            continue
        if geom_type == 'Polygon' and len(pts) < 3:
            skipped += 1
            continue
        if geom_type == 'LineString':
            # PolyLine / PolyLineZ / PolyLineM / etc — shapeType 3 = PolyLine
            if shape.shapeType in (3, 13, 23):  # PolyLine, PolyLineZ, PolyLineM
                # parts separate polylines
                rings = []
                if len(parts) == 1:
                    rings.append([(p[0], p[1]) for p in pts])
                else:
                    for k in range(len(parts)):
                        start = parts[k]
                        end = parts[k + 1] if k + 1 < len(parts) else len(pts)
                        rings.append([(p[0], p[1]) for p in pts[start:end]])
                if len(rings) == 1:
                    geometry = {'type': 'LineString', 'coordinates': rings[0]}
                else:
                    geometry = {'type': 'MultiLineString', 'coordinates': rings}
            else:
                skipped += 1
                continue
        else:  # Polygon
            # Polygon / PolygonZ / PolygonM / etc — shapeType 5 = Polygon
            if shape.shapeType in (5, 15, 17, 25):  # Polygon variants
                rings = []
                if len(parts) == 1:
                    rings.append([(p[0], p[1]) for p in pts])
                else:
                    for k in range(len(parts)):
                        start = parts[k]
                        end = parts[k + 1] if k + 1 < len(parts) else len(pts)
                        rings.append([(p[0], p[1]) for p in pts[start:end]])
                if len(rings) == 1:
                    # close ring if needed
                    if rings[0][0] != rings[0][-1]:
                        rings[0].append(rings[0][0])
                    geometry = {'type': 'Polygon', 'coordinates': rings}
                else:
                    geometry = {'type': 'MultiPolygon', 'coordinates': [[r] for r in rings]}
            else:
                skipped += 1
                continue
        features.append({
            'type': 'Feature',
            'geometry': geometry,
            'properties': props,
        })
    print(f'    built: {len(features)}, skipped (too small): {skipped}, empty: {empty}, broken: {broken}')
    return features, field_names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='/tmp/geofabrik-paraguay', help='unzipped Geofabrik directory')
    ap.add_argument('--max-per-layer', type=int, default=200000)
    ap.add_argument('--only', default=None, help='comma-separated layer bases to extract (default: all)')
    args = ap.parse_args()

    src = Path(args.src)
    if not src.exists():
        print(f'Source directory not found: {src}', file=sys.stderr)
        print(f'Run: unzip paraguay-latest-free.shp.zip -d {src}', file=sys.stderr)
        return 1

    only = set(args.only.split(',')) if args.only else None

    for base, out_name, geom_type in LAYER_MAP:
        if only and base not in only:
            continue
        print(f'\n=== {base} → {out_name} ===')
        features, field_names = shp_to_features(src, base, geom_type, args.max_per_layer)
        if not features:
            continue
        geo = {
            'type': 'FeatureCollection',
            'metadata': {
                'source': 'OpenStreetMap via Geofabrik Paraguay',
                'extracted_at_utc': datetime.now(timezone.utc).isoformat(),
                'shp_base': base,
                'count': len(features),
                'fields': field_names,
            },
            'features': features,
        }
        out_path = OUT_DIR / out_name
        out_path.write_text(json.dumps(geo))
        print(f'    wrote {out_path} ({out_path.stat().st_size:,} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())