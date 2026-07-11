#!/usr/bin/env python3
"""tools/fetch_osm_roads.py

Fetch all major roads in Paraguay from Overpass API, write as GeoJSON LineString
layer ready for Leaflet polyline overlay.

Overpass query: way["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified"]
within Paraguay's admin boundary. Returns ~50-80K ways, but we limit to 80K and
filter to roads with names + a "fclass" tag for coloring.

Output: exports/web/data/roads.geojson (LineString features)

Usage:
  python3 tools/fetch_osm_roads.py [--bbox "west,south,east,north"] [--max 80000]
"""
import argparse
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('/root/paraguay-geodata')
OUT = ROOT / 'exports/web/data/roads.geojson'

# Paraguay bbox (rough): -62.5W, -27.6S, -54.2E, -19.3N
PY_BBOX = '-62.5,-27.6,-54.2,-19.3'

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'
UA = 'Mozilla/5.0 (X11; Linux x86_64) Python/OSMRoadsFetcher'


def query_overpass(q: str) -> dict:
    data = urllib.parse.urlencode({'data': q}).encode('ascii')
    req = urllib.request.Request(OVERPASS_URL, data=data, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bbox', default=PY_BBOX)
    ap.add_argument('--max', type=int, default=80000)
    args = ap.parse_args()

    bbox = args.bbox
    q = f"""
    [out:json][timeout:240];
    (
      way["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|track|path|service|footway"]
         ({bbox});
    );
    out geom;
    """

    print(f'Querying Overpass bbox={bbox}, max {args.max} ways ...')
    print(f'Query length: {len(q)} chars')
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
    # Re-fetch geometry where missing
    missing = []
    for el in elements:
        if el.get('type') == 'way' and 'geometry' not in el:
            missing.append(el['id'])
    # For simplicity, query the missing nodes separately
    if missing:
        print(f'Refetching {len(missing)} missing node coordinates...')
        ids_str = ','.join(str(i) for i in missing[:5000])
        q2 = f'[out:json][timeout:60];node(id:{ids_str});out;'
        try:
            data2 = query_overpass(q2)
            for el in data2.get('elements', []):
                if el.get('type') == 'node':
                    nodes[el['id']] = (el['lon'], el['lat'])
        except Exception as e:
            print(f'  node refetch error (continuing): {e}')

    # Build features
    features = []
    skipped = 0
    for el in elements:
        if el.get('type') != 'way':
            continue
        geom = el.get('geometry')
        if not geom:
            # reconstruct from node refs
            refs = el.get('nodes', [])
            coords = [nodes.get(nid) for nid in refs if nid in nodes]
            if len(coords) < 2:
                skipped += 1
                continue
            geom = [{'lat': c[1], 'lon': c[0]} for c in coords]
        coords = [(p['lon'], p['lat']) for p in geom]
        if len(coords) < 2:
            skipped += 1
            continue
        tags = el.get('tags') or {}
        fclass = tags.get('highway', 'unknown')
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'LineString', 'coordinates': coords},
            'properties': {
                'osm_id': el['id'],
                'fclass': fclass,
                'name': tags.get('name'),
                'ref': tags.get('ref'),
                'surface': tags.get('surface'),
                'lanes': tags.get('lanes'),
                'oneway': tags.get('oneway'),
                'maxspeed': tags.get('maxspeed'),
                'bridge': tags.get('bridge') == 'yes',
                'tunnel': tags.get('tunnel') == 'yes',
            },
        })
        if len(features) >= args.max:
            print(f'  hit max {args.max}, stopping')
            break

    # Class summary
    from collections import Counter
    class_counts = Counter(f['properties']['fclass'] for f in features)
    print(f'\nFeatures built: {len(features)} (skipped {skipped})')
    print('  by highway class:')
    for k, v in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f'    {v:6d}  {k}')

    geo = {
        'type': 'FeatureCollection',
        'metadata': {
            'source': 'OpenStreetMap via Overpass API',
            'fetched_at_utc': datetime.now(timezone.utc).isoformat(),
            'bbox': bbox,
            'count': len(features),
        },
        'features': features,
    }
    OUT.write_text(json.dumps(geo))
    print(f'\n  wrote {OUT} ({OUT.stat().st_size:,} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())