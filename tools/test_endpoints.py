#!/usr/bin/env python3
"""tools/test_endpoints.py

End-to-end endpoint validation suite.
Run: python3 tools/test_endpoints.py

Tests:
  - Every data endpoint serves 200
  - Every GeoJSON has type=FeatureCollection + features array
  - properties_latest.geojson has all required fields
  - Manifest serves 200
  - Security headers present
  - Cache-Control has sensible TTL
  - Service Worker registered
"""
import json
import sys
import urllib.request
from pathlib import Path

BASE = 'https://geodata.paragu-ai.com'

ENDPOINTS = [
    ('/', 'html', True),
    ('/manifest.webmanifest', 'json', True),
    ('/sw.js', 'js', True),
    ('/data/properties_latest.geojson', 'geojson', True),
    ('/data/roads.geojson', 'geojson', True),
    ('/data/buildings_asuncion.geojson', 'geojson', True),
    ('/data/water.geojson', 'geojson', True),
    ('/data/gbif_paraguay.geojson', 'geojson', True),
    ('/data/tile_index.json', 'json', False),
    ('/data/priority_tiles.json', 'json', False),
    ('/data/bcp_snapshot.json', 'json', False),
    ('/data/nasa_power_asuncion.json', 'json', False),
    ('/data/inbio_zafra_2025_2026.json', 'json', False),
    ('/data/admin/catastro_dpto.geojson', 'geojson', True),
    ('/data/admin/catastro_dist.geojson', 'geojson', True),
    ('/data/admin/catastro_parcels_sample.geojson', 'geojson', True),
    ('/data/admin/catastro_urba.geojson', 'geojson', True),
    ('/data/admin/barrios_py.geojson', 'geojson', True),
    ('/data/ml/fair_price_model.json', 'json', False),
    ('/data/indigenous_territories.geojson', 'geojson', True),
    ('/data/climate_risk.geojson', 'geojson', True),
    ('/data/flood_risk.geojson', 'geojson', True),
    ('/data/data_freshness.json', 'json', False),
    ('/data/environment_meta.json', 'json', False),
]

REQUIRED_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
}

REQUIRED_PROPS_FIELDS = [
    'source', 'source_id', 'source_url', 'title',
    'price_pyg', 'price_usd', 'area_ha', 'bedrooms', 'state_province',
    'listing_type', 'property_type', 'images', 'city',
]


def get(url, headers=None):
    h = {'User-Agent': 'paraguay-geodata-test/1.0'}
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(BASE + url, headers=h)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, dict(r.headers), r.read()
    except Exception as e:
        return 0, {}, str(e).encode()


def main() -> int:
    pass_count = 0
    fail_count = 0
    failures = []

    print(f'=== Endpoint validator — {BASE} ===\n')

    # 1) Endpoint status + content validation
    for path, kind, is_required in ENDPOINTS:
        status, headers, body = get(path)
        if status != 200:
            print(f'  ✗ {status}  {path}')
            if is_required:
                fail_count += 1
                failures.append(f'{path} → {status}')
            continue

        size = len(body)
        ok = True
        err = None
        if kind == 'geojson':
            try:
                d = json.loads(body)
                if d.get('type') != 'FeatureCollection':
                    ok = False
                    err = f'type={d.get("type")}'
                elif not isinstance(d.get('features'), list):
                    ok = False
                    err = 'no features[] array'
                else:
                    cnt = len(d['features'])
                    print(f'  ✓ {status}  {size:>10,} bytes  {path}  ({cnt:,} features)')
            except Exception as e:
                ok = False
                err = f'invalid JSON: {e}'
        else:
            print(f'  ✓ {status}  {size:>10,} bytes  {path}')

        if not ok:
            print(f'  ✗ {status}  {path}  ({err})')
            if is_required:
                fail_count += 1
                failures.append(f'{path} → {err}')
        else:
            pass_count += 1

    # 2) properties_latest schema
    print('\n=== Schema validation ===')
    status, _, body = get('/data/properties_latest.geojson')
    if status == 200:
        d = json.loads(body)
        sample = d['features'][0]['properties']
        missing = [f for f in REQUIRED_PROPS_FIELDS if f not in sample]
        if missing:
            print(f'  ✗ properties_latest missing fields: {missing}')
            fail_count += 1
        else:
            print(f'  ✓ All {len(REQUIRED_PROPS_FIELDS)} required fields present')
            pass_count += 1

        # PII check
        pii_violations = []
        for f in d['features'][:500]:
            p = f.get('properties') or {}
            for k, v in p.items():
                if v and isinstance(v, str) and any(t in v.lower() for t in ['+595', 'phone', 'whatsapp']):
                    if not k.startswith('pii_') and 'pii' not in k.lower():
                        pii_violations.append((k, v[:50]))
        if pii_violations:
            print(f'  ✗ PII violations: {len(pii_violations)}')
            for v in pii_violations[:3]:
                print(f'    {v}')
            fail_count += 1
        else:
            print(f'  ✓ PII scrub: 0 violations in 500-feature sample')
            pass_count += 1

        # Coverage check
        with_imgs = sum(1 for f in d['features'] if f['properties'].get('images'))
        cov = 100 * with_imgs / len(d['features'])
        if cov > 95:
            print(f'  ✓ Image coverage: {cov:.1f}% ({with_imgs:,}/{len(d["features"]):,})')
            pass_count += 1
        else:
            print(f'  ✗ Image coverage: {cov:.1f}% (below 95%)')
            fail_count += 1

    # 3) Security headers
    print('\n=== Security headers ===')
    status, headers, _ = get('/')
    for h, expected in REQUIRED_HEADERS.items():
        actual = headers.get(h, '')
        if expected in actual:
            print(f'  ✓ {h}: {actual}')
            pass_count += 1
        else:
            print(f'  ✗ {h}: missing or wrong (expected: {expected}, got: {actual})')
            fail_count += 1

    # 4) Cache-Control
    cc = headers.get('Cache-Control', '')
    if 'max-age' in cc:
        print(f'  ✓ Cache-Control: {cc}')
        pass_count += 1
    else:
        print(f'  ✗ Cache-Control missing: {cc}')
        fail_count += 1

    # 5) SW registered
    status, headers, _ = get('/sw.js')
    ct = headers.get('Content-Type', '')
    if status == 200 and ('javascript' in ct or 'text' in ct):
        print(f'  ✓ Service Worker file accessible ({size} bytes, content-type: {ct})')
        pass_count += 1
    else:
        print(f'  ✗ Service Worker missing: {status}')
        fail_count += 1

    # Summary
    total = pass_count + fail_count
    print(f'\n{"=" * 70}')
    print(f'  RESULT: {pass_count}/{total} passed, {fail_count} failed')
    print(f'{"=" * 70}')

    if failures:
        print('\nFailures:')
        for f in failures:
            print(f'  - {f}')

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())