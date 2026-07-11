#!/usr/bin/env python3
"""tools/track_price_history.py

Track price changes for property listings over time.
Re-scrapes cached HTML and detects listings with reduced prices,
builds a price-history dataset.

Output: data/properties/price_history.json
{
  "as_of": "2026-07-11",
  "events": [
    {"id": "...", "source": "infocasas", "url": "...", "history": [{"date": "2026-07-11", "price_pyg": 450000000, "price_usd": 61644}]}
  ]
}

Usage:
  python3 tools/track_price_history.py [--baseline path/to/baseline.json]
"""
import argparse
import json
import re
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

ROOT = Path('/root/paraguay-geodata')
CACHE = ROOT / 'data/properties/cache'
OUT = ROOT / 'data/properties/price_history.json'
PROPERTIES = ROOT / 'exports/web/data/properties_latest.geojson'


def parse_price_infocasas(html: str) -> dict | None:
    """Extract price + listing_id from cached infocasas HTML."""
    # Price in PYG/USD
    pyg_m = re.search(r'(\d{1,3}(?:\.\d{3})+)\s*Gs', html)
    usd_m = re.search(r'US\$\s*([\d.,]+)', html) or re.search(r'\$\s*([\d.,]+)\s*USD', html)
    if not pyg_m and not usd_m:
        return None
    pyg = int(pyg_m.group(1).replace('.', '')) if pyg_m else None
    usd = None
    if usd_m:
        usd = int(re.sub(r'[^\d]', '', usd_m.group(1)))
    # Listing ID
    id_m = re.search(r'/(\d{4,})-[\w-]+\.html', html)
    return {
        'listing_id': id_m.group(1) if id_m else None,
        'price_pyg': pyg,
        'price_usd': usd,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', help='Previous baseline JSON')
    args = ap.parse_args()

    # Load current properties
    current = json.load(open(PROPERTIES))['features']
    current_by_id = {}
    for f in current:
        p = f['properties']
        sid = p.get('source_id') or p.get('id')
        current_by_id[sid] = p

    # Load baseline (previous snapshot)
    baseline_by_id = {}
    if args.baseline and Path(args.baseline).exists():
        baseline = json.load(open(args.baseline))['features']
        for f in baseline:
            p = f['properties']
            sid = p.get('source_id') or p.get('id')
            baseline_by_id[sid] = p

    # Find listings with price changes
    price_changes = []
    for sid, curr in current_by_id.items():
        if sid not in baseline_by_id:
            continue
        base = baseline_by_id[sid]
        if curr.get('price_usd') and base.get('price_usd'):
            delta = curr['price_usd'] - base['price_usd']
            if delta != 0:
                pct = (delta / base['price_usd']) * 100 if base['price_usd'] else 0
                price_changes.append({
                    'id': sid,
                    'source': curr.get('source'),
                    'url': curr.get('source_url'),
                    'title': curr.get('title', '')[:80],
                    'depto': curr.get('state_province'),
                    'previous_price_usd': base['price_usd'],
                    'current_price_usd': curr['price_usd'],
                    'delta_usd': delta,
                    'delta_pct': round(pct, 2),
                    'detected_utc': datetime.now(timezone.utc).isoformat(),
                })

    # Sort by biggest reductions
    price_changes.sort(key=lambda x: x['delta_pct'])

    out = {
        'as_of': datetime.now(timezone.utc).isoformat(),
        'total_properties': len(current_by_id),
        'price_changes_count': len(price_changes),
        'reductions': [c for c in price_changes if c['delta_usd'] < 0][:100],
        'increases': [c for c in price_changes if c['delta_usd'] > 0][:100],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))

    print(f'Wrote {OUT}')
    print(f'  {len(current_by_id)} properties compared')
    print(f'  {len(price_changes)} changed ({len(out["reductions"])} reductions, {len(out["increases"])} increases)')
    if out['reductions']:
        biggest = out['reductions'][0]
        print(f'  Biggest reduction: {biggest["title"]}: ${biggest["previous_price_usd"]:,.0f} → ${biggest["current_price_usd"]:,.0f} ({biggest["delta_pct"]:.1f}%)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())