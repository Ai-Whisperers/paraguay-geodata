#!/usr/bin/env python3
"""scripts/extract_images_from_cache.py

Walks through the infocasas detail-page HTML cache and adds an `images: [...]`
field to each property in properties_latest.geojson by matching the URL.

Each cached HTML has 30-40 image URLs (deduplicated property photos + branding
favicon). We extract them, filter out branding, and pick the top N property photos.

This is a one-shot script to upgrade the existing 676 listings; new scrapes
will have `_extract_images()` doing this inline.
"""
import json
import re
import sys
from pathlib import Path
from collections import OrderedDict

ROOT = Path('/root/paraguay-geodata')
CACHE_DIR = ROOT / 'data/properties/cache/infocasas'
GEOJSON = ROOT / 'exports/web/data/properties_latest.geojson'

# Branding/logo/whatsapp-image patterns to filter out (not property photos)
BRAND_PATTERNS = [
    re.compile(r'/isotipo', re.I),
    re.compile(r'/logo-?infocasas', re.I),
    re.compile(r'/@2x\.png', re.I),
    re.compile(r'/favicon', re.I),
    re.compile(r'/apple-icon', re.I),
    re.compile(r'/manifest', re.I),
    re.compile(r'fincaraiz\.com\.co/web/', re.I),  # branding CDN
]

# Common infocasas photo patterns (cdn1/cdn2/cdn3.infocasas.com.uy)
PHOTO_RE = re.compile(
    r'https?://cdn[0-9]?\.infocasas\.com\.uy/repo/img/[a-z0-9_\-\.]+\.(?:jpg|jpeg|png|webp)',
    re.I,
)

# Cache filename pattern: the HTML file is named by SHA1 of "infocasas:<source_id>"
# The scrape script does:
#   id_for_url ... = "ic_" + hashlib.sha1(("infocasas:" + source_id).encode()).hexdigest()[:12]
# But filenames here are full 16-char hash. Use SHA1 from source_id → derive cache filename.
import hashlib

def cache_filename_for_source_url(source_url: str) -> str:
    h = hashlib.sha1(source_url.encode('utf-8')).hexdigest()[:16]
    return f'{h}.html'

def extract_property_photos(html: str, max_n: int = 8) -> list[str]:
    """Pull out unique property image URLs from a detail page."""
    all_imgs = PHOTO_RE.findall(html)
    seen = OrderedDict()
    for u in all_imgs:
        if not any(p.search(u) for p in BRAND_PATTERNS):
            if u not in seen:
                seen[u] = True
        if len(seen) >= max_n:
            break
    return list(seen.keys())

def main() -> int:
    d = json.load(open(GEOJSON))
    features = d['features']
    print(f'Features: {len(features)}')

    matched = 0
    with_images = 0
    misses = 0
    for f in features:
        p = f['properties']
        source = p.get('source', '')
        if source != 'infocasas':
            continue
        matched += 1
        sid = p.get('source_url', '')
        if not sid:
            misses += 1
            continue
        cf = CACHE_DIR / cache_filename_for_source_url(sid)
        if not cf.exists():
            misses += 1
            continue
        html = cf.read_text(errors='ignore')
        photos = extract_property_photos(html, max_n=8)
        if photos:
            p['images'] = photos
            with_images += 1
    print(f'  infocasas features: {matched}')
    print(f'  cache miss (no HTML): {misses}')
    print(f'  enriched with images: {with_images}')

    out = json.dumps(d, indent=2, ensure_ascii=False)
    GEOJSON.write_text(out)
    print(f'  wrote {GEOJSON} ({len(out):,} bytes)')
    return 0

if __name__ == '__main__':
    sys.exit(main())