#!/usr/bin/env python3
"""tools/fetch_clasipar_sitemap.py

Download the Clasipar Paraguay sitemap shards, extract property listing URLs,
and emit a list of URLs we should later crawl for detail-page data.

Sitemap index: https://clasipar.paraguay.com/sitemap/index.xml
Lists ~1,610 shards ads1.xml.gz ... adsN.xml.gz.
Each shard ~1MB compressed, ~200-350 property URLs.
Total estimated: 400K+ property listing URLs.

We only download the index + a sample of shards here, and emit a JSON list.
A separate script (fetch_clasipar_detail.py) handles per-URL parsing in
batch with throttling. This script just produces the URL inventory.

Output: data/properties/clasipar_urls.json
{
  "fetched_at_utc": "...",
  "shards_total": 1610,
  "shards_scanned": <n>,
  "url_count": <n>,
  "urls": ["https://clasipar.paraguay.com/inmuebles/...", ...]
}

Usage:
  python3 tools/fetch_clasipar_sitemap.py --shards all       # full download (~2-4 hours)
  python3 tools/fetch_clasipar_sitemap.py --shards 50        # first 50 shards (~50K URLs)
"""
import argparse
import gzip
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/paraguay-geodata')
OUT_URLS = ROOT / 'data/properties/clasipar_urls.json'

INDEX_URL = 'https://clasipar.paraguay.com/sitemap/index.xml'
UA = 'Mozilla/5.0 (X11; Linux x86_64) Python/ClasiparSitemapFetcher'

# Match /inmuebles/<type>/<slug>-<id>
PROP_URL_RE = re.compile(r'https://clasipar\.paraguay\.com/inmuebles/[a-z\-]+/[a-z0-9\-]+-\d{4,}')


def fetch(url: str, timeout: int = 30) -> bytes:
    # No Accept-Encoding: gzip — when the server gzips, urllib auto-decompresses
    # AND keeps Content-Encoding header set, which corrupts our downstream
    # decode assumptions. Pass-through is cleaner for sitemap shards where we
    # explicitly call gzip.decompress().
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--shards', default='50', help='"all" or integer number of shards to scan')
    ap.add_argument('--sleep', type=float, default=0.5, help='sleep between shard fetches')
    ap.add_argument('--out', default=str(OUT_URLS), help='output path')
    args = ap.parse_args()

    print(f'Fetching sitemap index: {INDEX_URL}')
    idx_bytes = fetch(INDEX_URL)
    idx_xml = idx_bytes.decode('utf-8', errors='ignore')
    # find all shard URLs ads1.xml.gz ... ads1610.xml.gz
    # Note: index XML uses single-quoted namespace xmlns='...' so we just match <loc>...</loc>
    shards_all = re.findall(r'<loc>(https?://clasipar\.paraguay\.com/sitemap/[^<]+\.xml\.gz)</loc>', idx_xml)
    print(f'  shards_all (incl categories/landings): {len(shards_all)}')
    # filter to ads shards only
    shards = [u for u in shards_all if '/ads' in u]
    print(f'  ads shards: {len(shards)}')

    if args.shards != 'all':
        n = int(args.shards)
        shards = shards[:n]
        print(f'  scanning first {len(shards)} shards')

    all_urls = []
    for i, shard_url in enumerate(shards, 1):
        try:
            gz = fetch(shard_url)
            xml = gzip.decompress(gz).decode('utf-8', errors='ignore')
            found = PROP_URL_RE.findall(xml)
            all_urls.extend(found)
            if i % 10 == 0 or i == len(shards):
                print(f'  shard {i}/{len(shards)}: +{len(found)}  total={len(all_urls)}')
            time.sleep(args.sleep)
        except Exception as e:
            print(f'  shard {i} failed: {e}')
            continue

    # dedupe (some listings appear in multiple shards)
    seen = set()
    deduped = []
    for u in all_urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    print(f'\n  raw URLs: {len(all_urls)}')
    print(f'  unique URLs: {len(deduped)}')

    out = {
        'fetched_at_utc': datetime.now(timezone.utc).isoformat(),
        'shards_total_indexed': len(re.findall(r'<loc>(https?://clasipar\.paraguay\.com/sitemap/ads\d+\.xml\.gz)</loc>', idx_xml)),
        'shards_scanned': len(shards),
        'url_count': len(deduped),
        'urls': deduped,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f'  wrote {out_path} ({out_path.stat().st_size:,} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())