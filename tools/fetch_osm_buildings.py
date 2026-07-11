#!/usr/bin/env python3
"""tools/fetch_osm_buildings.py

Fetch building footprint polygons from OSM Overpass for Asunción (or any bbox).
Output: exports/web/data/buildings_<area>.geojson with Polygon/MultiPolygon features.

Used to provide urban density viz alongside the property listings.

Usage:
  python3 tools/fetch_osm_buildings.py [--bbox "west,south,east,north"] [--name asuncion] [--max 100000]
"""
import argparse
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path('/root/paraguay-geodata')

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'
UA = 'Mozilla/5.0 (X11; Linux x86_64) Python/OSMBuildingsFetcher'

# Greater Asunción metro bbox: roughly (24.95W, -25.50S, -57.30W, -25.10N)
ASUNCION_BBOX = '-57.75,-25.55,-57.45,-25.15'


def query_overpass(q: str) -> dict:
    data = urllib.parse.urlencode({'data': q}).encode('ascii')
    req = urllib.request.Request(OVERPASS_URL, data=data, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bbox', default=ASUNCION_BBOX)
    ap.add_argument('--name', default='asuncion')
    ap.add_argument('--max', type=int, default=100000)
    args = ap.parse_args()

    out = ROOT / 'exports/web/data' / f'buildings_{args.name}.geojson'

    q = f"""
    [out:json][timeout:240];
    (
      way["building"]
         ({args.bbox});
    );
    out geom;
    """

    print(f'Querying Overpass bbox={args.bbox}, name={args.name}, max={args.max} ...')
    try:
        data = query_overpass(q)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1

    elements = data.get('elements', [])
    print(f'Got {len(elements)} elements')

    # Build node lookup
    nodes = {}
    for el in elements:
        if el.get('type') == 'node':
            nodes[el['id']] = (el['lon'], el['lat'])

    features = []
    skipped = 0
    class_counts = Counter()
    for el in elements:
        if el.get('type') != 'way':
            continue
        geom = el.get('geometry')
        if not geom:
            refs = el.get('nodes', [])
            coords = [nodes.get(nid) for nid in refs if nid in nodes]
            if len(coords) < 3:
                skipped += 1
                continue
            geom = [{'lat': c[1], 'lon': c[0]} for c in coords]
        coords = [(p['lon'], p['lat']) for p in geom]
        if len(coords) < 3:
            skipped += 1
            continue
        # close ring if not already
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        tags = el.get('tags') or {}
        btype = tags.get('building', 'yes')
        class_counts[btype] += 1
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Polygon', 'coordinates': [coords]},
            'properties': {
                'osm_id': el['id'],
                'building': btype,
                'name': tags.get('name'),
                'levels': tags.get('building:levels'),
                'height': tags.get('height'),
                'amenity': tags.get('amenity'),
                'shop': tags.get('shop'),
                'office': tags.get('office'),
                'residential': tags.get('residential'),
            },
        })
        if len(features) >= args.max:
            print(f'  hit max {args.max}')
            break

    print(f'\nFeatures built: {len(features)} (skipped {skipped})')
    print('  by building type:')
    for k, v in sorted(class_counts.items(), key=lambda x: -x[1])[:15]:
        print(f'    {v:6d}  {k}')

    geo = {
        'type': 'FeatureCollection',
        'metadata': {
            'source': 'OpenStreetMap via Overpass API',
            'fetched_at_utc': datetime.now(timezone.utc).isoformat(),
            'bbox': args.bbox,
            'count': len(features),
        },
        'features': features,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(geo))
    print(f'\n  wrote {out} ({out.stat().st_size:,} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())