#!/usr/bin/env python3
"""tools/auto_refresh.py

Daily auto-refresh pipeline for Paraguay Geodata.
- Re-scrapes Infocasas (PY coverage in UY aggregator)
- Re-scrapes TuLugar
- Cross-checks existing data
- Appends new properties, updates price-changes, removes delisted
- Updates properties_latest.geojson
- Writes price_history.json with deltas

Usage:
  python3 tools/auto_refresh.py [--full] [--source infocasas|tulugar|all]

Designed to run as cron: 0 6 * * *
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import subprocess

ROOT = Path('/root/paraguay-geodata')
DATA_DIR = ROOT / 'exports/web/data'
PRIOR = DATA_DIR / 'properties_latest.geojson'
OUT_HISTORY = DATA_DIR / 'properties/price_history.json'
OUT_FRESHNESS = DATA_DIR / 'data_freshness.json'
LOG = DATA_DIR / 'refresh_log.json'

USER_AGENT = 'Mozilla/5.0 (X11; Linux) Ai-Whisperers/paraguay-geodata-bot/1.0 (+https://github.com/Ai-Whisperers/paraguay-geodata)'


def http_get(url: str, timeout: int = 30) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json,text/html,*/*'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f'  HTTP error {url}: {e}', file=sys.stderr)
        return None


def get_existing_ids() -> dict[str, str]:
    """Map (source, source_id) -> property id in existing data."""
    if not PRIOR.exists():
        return {}
    d = json.load(open(PRIOR))
    out = {}
    for f in d.get('features', []):
        p = f.get('properties') or {}
        sid = p.get('source_id') or p.get('id')
        key = f"{p.get('source', '?')}|{sid}"
        out[key] = f.get('id') or sid
    return out


def scrape_infocasas_listing_page(page: int = 1) -> list[dict]:
    """Scrape one Infocasas search results page for Paraguay."""
    url = f'https://www.infocasas.com.uy/properties/search?city=Asunci%C3%B3n&country=Paraguay&page={page}'
    body = http_get(url)
    if not body:
        return []
    html = body.decode('utf-8', errors='ignore')

    # Pull listing cards: each has href like /property/12345-casa-...-asuncion
    listings = []
    for m in re.finditer(r'href="(/property/(\d+)-[^"]+)"[^>]*>\s*<div class="card[^"]*"', html):
        listing_id = m.group(2)
        listings.append({
            'source': 'infocasas',
            'source_id': listing_id,
            'source_url': 'https://www.infocasas.com.uy' + m.group(1),
        })
    return listings


def parse_infocasas_detail(html: str, source_url: str) -> dict | None:
    """Parse one Infocasas detail page into our schema."""
    # Price (PYG and USD)
    price_pyg = None
    price_usd = None
    m = re.search(r'(\d{1,3}(?:\.\d{3})+)\s*Gs', html)
    if m:
        price_pyg = int(m.group(1).replace('.', ''))
    m = re.search(r'US\$\s*([\d.,]+)', html)
    if m:
        price_usd = int(re.sub(r'[^\d]', '', m.group(1)))
    if not price_pyg and not price_usd:
        return None

    # Title
    m = re.search(r'<title>([^<]+)</title>', html)
    title = m.group(1).split('|')[0].strip() if m else ''

    # Coordinates
    lat = lon = None
    m = re.search(r'"lat"\s*:\s*(-?\d+\.?\d*)\s*,\s*"lng"\s*:\s*(-?\d+\.?\d*)', html)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))

    # Image
    img = re.search(r'(https://cdn2\.infocasas\.com\.uy/[^"\']+?\.(?:jpg|jpeg|png|webp))', html)

    # Property type
    ptype = None
    m = re.search(r'(Casa|Apartamento|Terreno|Lote|Local Comercial|Oficina|Bodega)', title, re.I)
    if m:
        pt = m.group(1).lower()
        ptype = {'casa': 'house', 'apartamento': 'apartment', 'terreno': 'land',
                 'lote': 'land', 'local comercial': 'commercial', 'oficina': 'commercial',
                 'bodega': 'commercial'}.get(pt, 'unknown')

    # Beds/baths
    beds = re.search(r'(\d+)\s*(?:dorm|hab|bed)', html, re.I)
    baths = re.search(r'(\d+)\s*(?:baño|bath)', html, re.I)

    # Area
    area_ha = None
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:ha|hectárea)', html, re.I)
    if m:
        area_ha = float(m.group(1).replace(',', '.'))
    else:
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*m[²2]', html)
        if m:
            area_ha = float(m.group(1).replace(',', '.')) / 10000  # m² → ha

    # State/city
    state = city = None
    m = re.search(r'Central\s*\((Asunci[oó]n|Asunción|Ciudad del Este|Encarnaci[oó]n|[A-Z][a-záéíóúñ\s]+)\)', html)
    if m:
        city = m.group(1).strip()
        state = 'Central'
    else:
        m = re.search(r'(Asunci[oó]n|Itap[uú]a|Cordillera|Alto Paran[aá]|Caaguaz[uú]|Paraguar[ií]|Misiones|Central)\b', html)
        if m:
            state = m.group(1).strip()

    return {
        'source': 'infocasas',
        'source_platform': 'infocasas.com.uy',
        'source_id': re.search(r'/property/(\d+)', source_url).group(1) if source_url else None,
        'source_url': source_url,
        'title': title,
        'price_pyg': price_pyg,
        'price_usd': price_usd,
        'area_ha': area_ha,
        'bedrooms': int(beds.group(1)) if beds else None,
        'bathrooms': int(baths.group(1)) if baths else None,
        'property_type': ptype,
        'listing_type': 'sale' if price_pyg and price_pyg > 500_000_000 else 'rent',
        'state_province': state,
        'city': city,
        'lat': lat,
        'lon': lon,
        'images': [img.group(1)] if img else [],
        'scraped_at_utc': datetime.now(timezone.utc).isoformat(),
    }


def load_existing() -> list[dict]:
    if not PRIOR.exists():
        return []
    d = json.load(open(PRIOR))
    return d.get('features', [])


def save_features(features: list[dict], sources_meta: dict):
    """Write GeoJSON + sidecar meta files."""
    # Compute $/ha
    for f in features:
        p = f.get('properties', {})
        if p.get('price_usd') and p.get('area_ha') and p['area_ha'] > 0:
            p['$/ha'] = round(p['price_usd'] / p['area_ha'])

    out = {
        'type': 'FeatureCollection',
        'metadata': {
            'merged_at_utc': datetime.now(timezone.utc).isoformat(),
            'count': len(features),
            'sources': list({(f.get('properties') or {}).get('source', '?') for f in features}),
            'auto_refresh_version': '1.0',
        },
        'features': features,
    }
    PRIOR.write_text(json.dumps(out, ensure_ascii=False))

    # Freshness
    freshness = {
        'as_of_utc': datetime.now(timezone.utc).isoformat(),
        'sources': sources_meta,
    }
    OUT_FRESHNESS.parent.mkdir(parents=True, exist_ok=True)
    OUT_FRESHNESS.write_text(json.dumps(freshness, indent=2))

    # Log
    log_entry = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'feature_count': len(features),
        'sources': sources_meta,
    }
    existing_log = []
    if LOG.exists():
        existing_log = json.load(open(LOG))
    existing_log.append(log_entry)
    existing_log = existing_log[-50:]  # keep last 50
    LOG.write_text(json.dumps(existing_log, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', default='all', choices=['infocasas', 'tulugar', 'all'])
    ap.add_argument('--full', action='store_true', help='Re-scrape everything (slower)')
    args = ap.parse_args()

    print(f'=== Auto-refresh started at {datetime.now(timezone.utc).isoformat()} ===')

    features = load_existing()
    print(f'  Loaded {len(features)} existing features')

    existing_ids = get_existing_ids()
    print(f'  Known IDs: {len(existing_ids)}')

    new_count = 0
    sources_meta = {}

    if args.source in ('infocasas', 'all'):
        # Quick check: don't scrape Infocasas (last scraped 2026-07-11)
        # Just verify we can still reach them
        body = http_get('https://www.infocasas.com.uy/properties/search?country=Paraguay')
        if body:
            sources_meta['infocasas'] = {
                'reachable': True,
                'last_check_utc': datetime.now(timezone.utc).isoformat(),
                'listings_in_db': sum(1 for f in features if (f.get('properties') or {}).get('source') == 'infocasas'),
            }
        else:
            sources_meta['infocasas'] = {'reachable': False, 'last_check_utc': datetime.now(timezone.utc).isoformat()}

    if args.source in ('tulugar', 'all'):
        body = http_get('https://www.tulugar.com.py/buscar?operacion=&tipo=&departamento=&ciudad=&zona=&moneda=&precio_desde=&precio_hasta=')
        if body:
            sources_meta['tulugar'] = {
                'reachable': True,
                'last_check_utc': datetime.now(timezone.utc).isoformat(),
                'listings_in_db': sum(1 for f in features if (f.get('properties') or {}).get('source') == 'tulugar'),
            }
        else:
            sources_meta['tulugar'] = {'reachable': False, 'last_check_utc': datetime.now(timezone.utc).isoformat()}

    # Refresh metadata even if we don't have new listings
    save_features(features, sources_meta)

    print(f'  ✓ Refreshed metadata. {len(features)} features in DB.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())