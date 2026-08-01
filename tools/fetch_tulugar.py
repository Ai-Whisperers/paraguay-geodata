#!/usr/bin/env python3
"""tools/fetch_tulugar.py

Pull every property listing from TuLugar.com /api/listings, transform to our
canonical GeoJSON feature shape, and write to data/properties/tulugar_snap.json
plus exports/web/data/properties_tulugar.geojson.

TuLugar is a meta-aggregator: each listing has a `source_platform` field
(century21.com.py, infocasas.com.py, etc.) so we can dedupe cross-source
later. TuLugar also pre-converts PYG→USD via `price_usd`, and embeds
lat/lon for most listings.

Output schema (per feature.properties):
  id            "tl_" + 12-char SHA1 hash
  source        "tulugar"
  source_id     UUID (TuLugar's id)
  source_url    TuLugar URL
  source_platform  original portal (century21.com.py / infocasas / etc.)
  scraped_at_utc ISO timestamp
  title         listing title
  description   HTML description
  lat, lon      coordinates
  city, neighborhood, state_province, country
  address       street address
  listing_type  "rent" | "sale" | "short_rent"
  property_type "house" | "apartment" | "land" | "commercial"
  price_pyg     raw PYG price
  price_usd     TuLugar's auto-converted USD price
  bedrooms, bathrooms, area_sqm, lot_size_sqm, parking_spaces
  features[]    tag array
  currency      "PYG" | "USD"
  verified      bool
  images[]      up to 8 CDN image URLs (cdn.tulugar.com)
  source_agent  name + whatsapp

Usage:
  python3 tools/fetch_tulugar.py --limit-total 20000 [--limit 100] [--sleep 1.0]
"""
import argparse
import hashlib
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/paraguay-geodata')
OUT_JSON = ROOT / 'data/properties/tulugar_snap.json'
OUT_GEOJSON = ROOT / 'exports/web/data/properties_tulugar.geojson'

API_BASE = 'https://tulugar.com/api/v1/listings'
UA = 'Mozilla/5.0 (X11; Linux x86_64) Python/TuLugarFetcher'

# TuLugar (Aug 2026 schema): `data[]` with each item having price/currency,
# latitude/longitude, slug (no separate source_platform field — every listing
# is first-party).  Older fields (source_agent, description, og_image_url)
# have been removed.
FX_PYG_PER_USD = 7_500.0


def fetch_page(limit: int, offset: int) -> dict:
    url = f'{API_BASE}?limit={limit}&offset={offset}'
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def to_feature(item: dict) -> dict | None:
    lat = item.get('latitude')
    lon = item.get('longitude')
    if lat is None or lon is None:
        return None
    sid = item.get('id', '')
    slug = item.get('slug') or sid
    listing_type = item.get('listing_type', 'sale')
    ptype = item.get('property_type', 'unknown')

    # Single `price` field + `currency` discriminator.
    raw_price = item.get('price')
    currency = (item.get('currency') or '').upper()
    price_pyg = raw_price if currency == 'PYG' else None
    price_usd = raw_price if currency == 'USD' else (
        round(raw_price / FX_PYG_PER_USD, 2) if (raw_price and currency == 'PYG') else None
    )

    # Build the dedupe-friendly ID
    h = hashlib.sha1(('tulugar:' + sid).encode()).hexdigest()[:12]

    # New URL pattern: /propiedades/ (plural).  Keep the historical
    # /propiedad/ pattern in mind — the site 301s to the new path, but we
    # ship the canonical URL so crawlers don't double-redirect.
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
        "properties": {
            "id": "tl_" + h,
            "source": "tulugar",
            "source_id": sid,
            "source_url": f"https://tulugar.com/es/paraguay/propiedades/{slug}",
            "source_platform": None,
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "title": item.get('title'),
            "lat": float(lat),
            "lon": float(lon),
            "city": item.get('city'),
            "neighborhood": item.get('neighborhood'),
            "state_province": None,  # not exposed by v1 API; canonicalizer fills it
            "country": item.get('country'),
            "listing_type": listing_type,
            "property_type": ptype,
            "currency": currency or None,
            "price_pyg": price_pyg,
            "price_usd": price_usd,
            "bedrooms": item.get('bedrooms'),
            "bathrooms": item.get('bathrooms'),
            "area_sqm": item.get('area_sqm'),
            "lot_size_sqm": item.get('lot_size_sqm'),
            "covered_area_sqm": item.get('covered_area_sqm'),
            "parking_spaces": item.get('parking_spaces'),
            "condition": item.get('condition'),
            "furnished": item.get('furnished'),
            "verified": bool(item.get('verified', False)),
            "features": [],  # v1 API no longer exposes features
            "images": (item.get('images') or [])[:8],
            "views": item.get('views'),
            "favorites_count": item.get('favorites_count'),
            "created_at": item.get('created_at'),
            "updated_at": item.get('updated_at'),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=100, help='per-page limit (max 100)')
    ap.add_argument('--limit-total', type=int, default=20000, help='max total records')
    ap.add_argument('--sleep', type=float, default=1.0, help='seconds between page fetches')
    args = ap.parse_args()

    all_features = []
    offset = 0
    pages = 0
    while len(all_features) < args.limit_total:
        try:
            data = fetch_page(args.limit, offset)
        except Exception as e:
            print(f'  page fetch error @ offset={offset}: {e}')
            time.sleep(5)
            continue
        items = data.get('data') or []
        if not items:
            print(f'  empty page @ offset={offset}, stopping')
            break
        for it in items:
            feat = to_feature(it)
            if feat:
                all_features.append(feat)
        pages += 1
        print(f'  page {pages}: offset={offset}  items={len(items)}  kept={len(all_features)}')
        offset += args.limit
        time.sleep(args.sleep)
        if len(items) < args.limit:
            print('  short page (last page reached)')
            break

    geo = {"type": "FeatureCollection", "features": all_features}
    OUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_GEOJSON.write_text(json.dumps(geo, indent=2, ensure_ascii=False))

    # also keep a flat JSON for downstream merges
    raw = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(), "count": len(all_features), "features": all_features}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(raw, indent=2, ensure_ascii=False))

    print(f'\n  wrote {len(all_features)} features to {OUT_GEOJSON}')
    print(f'  wrote {OUT_JSON}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())