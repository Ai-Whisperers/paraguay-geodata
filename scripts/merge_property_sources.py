#!/usr/bin/env python3
"""scripts/merge_property_sources.py

Combine 3 listing sources (infocasas, tulugar, future clasipar) into a single
unified properties_latest.geojson with consistent schema + cross-source dedupe.

Strategy:
  1. Load all 3 GeoJSON sources
  2. Normalize to a canonical schema (keys we know about)
  3. Dedupe by:
     a) source_url (exact match wins)
     b) lat/lon round-4 (~11m radius) + listing_type
  4. TuLugar wins when conflict (richer schema, pre-converted USD)
  5. Clasipar URL-only gets minimal stub (no detail fetched yet)
  6. Write merged GeoJSON + per-source count summary

Canonical schema for each feature.properties:
  id, source, source_id, source_url, source_platform,
  scraped_at_utc, title, description,
  lat, lon, address, city, neighborhood, state_province, country,
  listing_type, property_type,
  currency, price_pyg, price_usd,
  bedrooms, bathrooms, area_sqm, area_ha, lot_size_sqm,
  $/ha, parking_spaces, year_built, condition, furnished,
  verified, features[], images[],
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/paraguay-geodata')
PUBLIC_DATA = ROOT / 'exports/web/data'
INTERNAL_DATA = ROOT / 'data/properties'

OUT_GEOJSON = PUBLIC_DATA / 'properties_latest.geojson'

INFOCASAS = PUBLIC_DATA / 'properties_latest.geojson'
TULUGAR = PUBLIC_DATA / 'properties_tulugar.geojson'
CLASIPAR_URLS = INTERNAL_DATA / 'clasipar_urls.json'


def _round_coord(x, digits=4):
    if x is None:
        return None
    try:
        return round(float(x), digits)
    except Exception:
        return None


def _normalize_infocasas(f):
    p = f['properties']
    return {
        'id': p.get('id'),
        'source': 'infocasas',
        'source_id': p.get('source_id'),
        'source_url': p.get('source_url'),
        'source_platform': 'infocasas.com.py',
        'scraped_at_utc': p.get('scraped_at_utc'),
        'title': p.get('title'),
        'description': None,
        'lat': _round_coord(f['geometry']['coordinates'][1]),
        'lon': _round_coord(f['geometry']['coordinates'][0]),
        'address': p.get('address'),
        'city': (p.get('address') or {}).get('city') if isinstance(p.get('address'), dict) else None,
        'neighborhood': None,
        'state_province': p.get('depto'),
        'country': 'Paraguay',
        'listing_type': 'sale',  # default; infocasas has rents but our cached data is sales
        'property_type': None,
        'currency': 'USD',
        'price_pyg': p.get('price_pyg'),
        'price_usd': p.get('price_usd'),
        'bedrooms': p.get('bedrooms'),
        'bathrooms': None,
        'area_sqm': (p.get('area_ha') or 0) * 10000 if p.get('area_ha') else None,
        'area_ha': p.get('area_ha'),
        'lot_size_sqm': None,
        '$/ha': p.get('$/ha'),
        'parking_spaces': None,
        'year_built': None,
        'condition': None,
        'furnished': None,
        'verified': False,
        'features': [],
        'images': p.get('images') or [],
    }


def _normalize_tulugar(f):
    p = f['properties']
    price_pyg = p.get('price_pyg')
    price_usd = p.get('price_usd')
    area_sqm = p.get('area_sqm')
    area_ha = (area_sqm / 10000.0) if area_sqm else None
    per_ha = None
    if price_usd and area_ha and area_ha > 0:
        per_ha = price_usd / area_ha
    elif price_pyg and area_ha and area_ha > 0:
        per_ha = (price_pyg / 7300) / area_ha  # rough PYG/USD 7300
    return {
        'id': p.get('id'),
        'source': 'tulugar',
        'source_id': p.get('source_id'),
        'source_url': p.get('source_url'),
        'source_platform': p.get('source_platform'),
        'source_agent': p.get('source_agent'),
        'source_agent_whatsapp': p.get('source_agent_whatsapp'),
        'scraped_at_utc': p.get('scraped_at_utc'),
        'title': p.get('title'),
        'description': p.get('description'),
        'lat': _round_coord(p.get('lat')),
        'lon': _round_coord(p.get('lon')),
        'address': p.get('address'),
        'city': p.get('city'),
        'neighborhood': p.get('neighborhood'),
        'state_province': p.get('state_province'),
        'country': p.get('country'),
        'listing_type': p.get('listing_type'),
        'property_type': p.get('property_type'),
        'currency': p.get('currency'),
        'price_pyg': price_pyg,
        'price_usd': price_usd,
        'bedrooms': p.get('bedrooms'),
        'bathrooms': p.get('bathrooms'),
        'area_sqm': area_sqm,
        'area_ha': area_ha,
        'lot_size_sqm': p.get('lot_size_sqm'),
        '$/ha': per_ha,
        'parking_spaces': p.get('parking_spaces'),
        'year_built': p.get('year_built'),
        'condition': p.get('condition'),
        'furnished': p.get('furnished'),
        'verified': p.get('verified', False),
        'features': p.get('features') or [],
        'images': p.get('images') or [],
        'og_image_url': p.get('og_image_url'),
    }


def _stub_clasipar(url):
    """A bare listing URL we haven't yet scraped. Stub it so we have it in
    the catalog and can later re-fetch detail pages."""
    # Extract last path component as a slug
    slug = url.rstrip('/').split('/')[-1]
    return {
        'id': 'cl_' + slug.split('-')[-1] if slug.split('-')[-1].isdigit() else 'cl_' + slug.replace('-', '_')[:16],
        'source': 'clasipar',
        'source_id': slug.split('-')[-1] if slug.split('-')[-1].isdigit() else slug,
        'source_url': url,
        'source_platform': 'clasipar.paraguay.com',
        'scraped_at_utc': None,
        'title': None,
        'description': None,
        'lat': None,
        'lon': None,
        'address': None,
        'city': None,
        'neighborhood': None,
        'state_province': None,
        'country': 'Paraguay',
        'listing_type': None,
        'property_type': None,
        'currency': None,
        'price_pyg': None,
        'price_usd': None,
        'bedrooms': None,
        'bathrooms': None,
        'area_sqm': None,
        'area_ha': None,
        'lot_size_sqm': None,
        '$/ha': None,
        'parking_spaces': None,
        'year_built': None,
        'condition': None,
        'furnished': None,
        'verified': False,
        'features': [],
        'images': [],
        '_pending_detail': True,  # marker that we haven't parsed the detail page yet
    }


def main() -> int:
    print('Loading sources...')
    rows = []

    if INFOCASAS.exists():
        d = json.load(open(INFOCASAS))
        for f in d.get('features', []):
            rows.append(_normalize_infocasas(f))
        print(f'  infocasas: {len(d["features"])} features')

    if TULUGAR.exists():
        d = json.load(open(TULUGAR))
        kept = 0
        for f in d.get('features', []):
            p = f.get('properties') or {}
            if p.get('lat') is None or p.get('lon') is None:
                continue  # TuLugar records without coords are useless for the map
            rows.append(_normalize_tulugar(f))
            kept += 1
        print(f'  tulugar (with coords): {kept} of {len(d["features"])}')

    if CLASIPAR_URLS.exists():
        d = json.load(open(CLASIPAR_URLS))
        n_before = len(rows)
        for u in d.get('urls', []):
            rows.append(_stub_clasipar(u))
        print(f'  clasipar URL stubs: +{len(rows) - n_before}')

    # Dedupe
    print(f'\nTotal before dedupe: {len(rows)}')

    # Pass 1: dedupe by source_url
    by_url = {}
    no_url = []
    for r in rows:
        u = r.get('source_url')
        if u:
            by_url.setdefault(u, []).append(r)
        else:
            no_url.append(r)
    deduped = []
    for u, group in by_url.items():
        if len(group) == 1:
            deduped.append(group[0])
        else:
            # multiple sources for same URL → keep the one with the most fields populated
            group.sort(key=lambda r: sum(1 for v in r.values() if v is not None and v != [] and v != {}), reverse=True)
            winner = dict(group[0])  # copy
            winner['_merged_from'] = sorted({g['source'] for g in group})
            # preserve images from all sources
            imgs = []
            seen_imgs = set()
            for g in group:
                for img in g.get('images') or []:
                    if img not in seen_imgs:
                        imgs.append(img)
                        seen_imgs.add(img)
            winner['images'] = imgs[:12]
            deduped.append(winner)

    # Pass 2: dedupe by (lat_round, lon_round, listing_type)
    # only for records that have lat/lon
    by_loc = {}
    no_loc = []
    for r in deduped:
        lat, lon = r.get('lat'), r.get('lon')
        if lat is not None and lon is not None:
            key = (lat, lon, r.get('listing_type') or 'sale')
            by_loc.setdefault(key, []).append(r)
        else:
            no_loc.append(r)

    final = []
    dup_loc = 0
    for key, group in by_loc.items():
        if len(group) == 1:
            final.append(group[0])
        else:
            dup_loc += 1
            # keep richest record (usually tulugar)
            group.sort(key=lambda r: sum(1 for v in r.values() if v is not None and v != [] and v != {}), reverse=True)
            final.append(group[0])

    final.extend(no_loc)

    print(f'  source_url dedupe: {len(rows) - len(deduped)} removed')
    print(f'  lat/lon dedupe: {dup_loc} groups merged')
    print(f'Final features: {len(final)}')

    # Write GeoJSON
    geo_features = []
    for r in final:
        if r.get('lat') is None or r.get('lon') is None:
            # Skip entries without coords (we can't put them on the map)
            continue
        # drop internal markers
        props = {k: v for k, v in r.items() if not k.startswith('_')}
        geo_features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [r['lon'], r['lat']]},
            'properties': props,
        })

    geo = {
        'type': 'FeatureCollection',
        'metadata': {
            'merged_at_utc': datetime.now(timezone.utc).isoformat(),
            'sources': ['infocasas', 'tulugar', 'clasipar'],
            'count': len(geo_features),
        },
        'features': geo_features,
    }

    OUT_GEOJSON.write_text(json.dumps(geo, indent=2, ensure_ascii=False))
    print(f'\n  wrote {OUT_GEOJSON} ({OUT_GEOJSON.stat().st_size:,} bytes, {len(geo_features)} features)')

    # Source breakdown
    counts = defaultdict(int)
    for f in geo_features:
        counts[f['properties']['source']] += 1
    print(f'\n  source breakdown: {dict(counts)}')

    # Save metadata separately for the viewer to display
    meta = {
        'merged_at_utc': geo['metadata']['merged_at_utc'],
        'sources': geo['metadata']['sources'],
        'count': geo['metadata']['count'],
        'breakdown': dict(counts),
        'pending_clasipar_detail': sum(1 for r in final if r.get('_pending_detail')),
    }
    (PUBLIC_DATA / 'properties_meta.json').write_text(json.dumps(meta, indent=2))
    print(f'  wrote {PUBLIC_DATA / "properties_meta.json"}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())