#!/usr/bin/env python3
"""tools/fetch_bienesonline.py

Scraper for paraguay.bienesonline.com — a Paraguayan real-estate
directory that primarily serves Catastro-derived listings.

Endpoint shape:
  Index page: https://paraguay.bienesonline.com/<category>/<operation>
  Categories: casas, terrenos, departamentos, locales, oficinas, galpones
  Operations: venta, alquiler

The site is server-rendered HTML (jQuery-only). Each index page lists
~15-50 listings with a `/propiedad/<slug>` detail link. The listings
typically include: location (with dept/district), price (often in gs.
or USD), total area in m², sometimes lat/lon (when an address lookup
succeeds), and rooms count.

NOTES:
  * The HTML uses inline images but no JS hydration. We can scrape all
    visible listings in O(N) pages.
  * The site does NOT have a sitemap; index pages are the only discovery
    surface.
  * Each page advertises "<N> Resultados" count. Pagination pattern
    is "?page=N" or "/page/N" depending on the server.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
UA = USER_AGENT
FX_PYG_PER_USD = 7_500.0

CATEGORIES = [
    ("casas", "house"),
    ("terrenos", "land"),
    ("departamentos", "apartment"),
    ("locales", "commercial"),
    ("oficinas", "commercial"),
    ("galpones", "commercial"),
    ("quintas", "house"),
    ("campos", "land"),
    ("edificios", "commercial"),
]
OPERATIONS = [
    ("venta", "sale"),
    ("alquiler", "rent"),
]


def _fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-PY,es;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        return body.decode("utf-8", errors="ignore") if isinstance(body, bytes) else body


# Per-category pages are paginated via ?page=<n>. The first page uses
# /<cat>/<op>; subsequent pages use /<cat>/<op>?page=<n>.
def page_urls(cat_slug: str, op_slug: str, max_pages: int) -> Iterator[str]:
    base = f"https://paraguay.bienesonline.com/{cat_slug}/{op_slug}"
    for p in range(1, max_pages + 1):
        yield f"{base}?page={p}" if p > 1 else base


# Find listing detail URLs in the page HTML.  The site uses
# `<a href="/propiedad/<slug>">...` and possibly label like
# `<a class="resultado-title" ...>`.
DETAIL_RE = re.compile(r'href="(/propiedad/[\w\-]+/?)"')
PRICE_RE = re.compile(r'(?:Gs\.?|PYG|gs\.?)\s*([\d.,]+)', re.I)
USD_RE = re.compile(r'(?:US\$|U\$S)\s*([\d.,]+)', re.I)
TOTAL_HITS_RE = re.compile(r'(\d{2,5})\s+(?:Resultados|resultados|Resultados\s+encontrados)', re.I)
AREAM_RE = re.compile(r'(\d+(?:[.,]\d+)?)\s*m[²2]', re.I)
HECTARE_RE = re.compile(r'(\d+(?:[.,]\d+)?)\s*(?:h[áaéc]|\bha\b)', re.I)


def _make_id(slug: str) -> str:
    return "bo_" + hashlib.sha1(("bienesonline:" + slug).encode()).hexdigest()[:12]


def _parse_detail_url(slug: str) -> str:
    return "https://paraguay.bienesonline.com/propiedad/" + slug.rstrip("/")


def _parse_price_text(t: str) -> tuple[int | None, float | None, str | None]:
    """Return (price_pyg, price_usd, currency)."""
    if not t:
        return None, None, None
    m = USD_RE.search(t)
    if m:
        try:
            usd = float(m.group(1).replace(".", "").replace(",", "."))
            return int(usd * FX_PYG_PER_USD), usd, "USD"
        except Exception:
            pass
    m = PRICE_RE.search(t)
    if m:
        try:
            pyg = int(m.group(1).replace(".", "").replace(",", ""))
            return pyg, pyg / FX_PYG_PER_USD, "PYG"
        except Exception:
            pass
    return None, None, None


def _extract_card(html: str, slug: str) -> dict | None:
    """Build a record from a single listing card block.

    The card pattern: a `<div class="...resultado...">` block with title,
    price, location, area.  We just regex over the full card text.
    """
    # Locate the card around this slug's anchor
    pat = re.compile(
        r'<a[^>]+href="(/propiedad/' + re.escape(slug) + r'/?)"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    link_match = pat.search(html)
    card_block_start = 0
    if link_match:
        card_block_start = max(0, link_match.start() - 4000)
    # card_block_end = link_match.end() + 2000 — for now just parse the
    # whole page text in a window around this link.
    card_text = html[card_block_start: card_block_start + 8000]
    card_text = re.sub(r"<[^>]+>", " | ", card_text)
    card_text = re.sub(r"\s+", " ", card_text).strip()

    title = ""
    m_title = re.search(r"<a[^>]+href=\"/propiedad/" + re.escape(slug) + r"/?\"[^>]*>(.*?)</a>", html, re.IGNORECASE | re.DOTALL)
    if m_title:
        title = re.sub(r"<[^>]+>", "", m_title.group(1)).strip()

    pyg, usd, curr = _parse_price_text(card_text)

    area_sqm = None
    m = AREAM_RE.search(card_text)
    if m:
        try:
            area_sqm = float(m.group(1).replace(",", "."))
        except Exception:
            pass
    if area_sqm is None:
        m = HECTARE_RE.search(card_text)
        if m:
            try:
                ha = float(m.group(1).replace(",", "."))
                area_sqm = ha * 10_000
            except Exception:
                pass

    location = ""
    m_loc = re.search(r'(?:Ubicado|Ubicada|en|zona)\s+(?:en\s+)?(?:el\s+|la\s+)?([\w\s,Á-Úá-ú.]+)', card_text, re.I)
    if m_loc:
        location = m_loc.group(1).strip()[:120]

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [None, None]},
        "properties": {
            "id": _make_id(slug),
            "source": "bienesonline",
            "source_id": slug,
            "source_url": _parse_detail_url(slug),
            "source_platform": "paraguay.bienesonline.com",
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "title": title[:200],
            "city": None,
            "state_province": None,
            "country": "Paraguay",
            "listing_type": "sale",
            "property_type": "unknown",
            "currency": curr,
            "price_pyg": pyg,
            "price_usd": round(usd, 2) if usd else None,
            "bedrooms": None,
            "bathrooms": None,
            "area_sqm": area_sqm,
            "area_ha": round(area_sqm / 10000, 4) if area_sqm else None,
            "images": [],
            "description": card_text[:1500],
            "lat": None,
            "lon": None,
            "_location_text": location,
        },
    }


def scrape(max_pages_per_cat: int = 5, sleep_s: float = 0.7) -> list[dict]:
    import time
    feats: list[dict] = []
    seen_slugs: set[str] = set()
    for cat_slug, cat_type in CATEGORIES:
        for op_slug, op_type in OPERATIONS:
            for page_url in page_urls(cat_slug, op_slug, max_pages_per_cat):
                try:
                    html = _fetch(page_url)
                except Exception as exc:
                    print(f"  warn {page_url}: {exc}", file=sys.stderr)
                    break
                if not html or len(html) < 1000:
                    break
                # Iterate over every listing URL on this page
                slugs = DETAIL_RE.findall(html)
                page_kept = 0
                for slug_full in slugs:
                    # slug_full may include subpath; we just need the last segment
                    slug = slug_full.rstrip("/").split("/")[-1]
                    if not slug or slug in seen_slugs:
                        continue
                    seen_slugs.add(slug)
                    feat = _extract_card(html, slug)
                    if feat is None:
                        continue
                    feat["properties"]["listing_type"] = op_type
                    feat["properties"]["property_type"] = cat_type
                    feats.append(feat)
                    page_kept += 1
                print(f"  {cat_slug}/{op_slug} {page_url[len('https://paraguay.bienesonline.com'):]}: {len(slugs)} listings → kept {page_kept}")
                if page_kept == 0 and " 0 Resultados" in html:
                    break
                if " 0 Resultados" in html:
                    break
                # Heuristic: stop early if the page doesn't include listings at all
                if page_kept == 0 and not slugs:
                    break
                time.sleep(sleep_s)
    return feats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-pages", type=int, default=3)
    ap.add_argument("--sleep", type=float, default=0.6)
    ap.add_argument("--output-dir", type=Path,
                    default=ROOT / "data/properties/snapshots")
    ap.add_argument("--no-fetch", action="store_true")
    args = ap.parse_args(argv)

    if args.no_fetch:
        feats = []
    else:
        feats = scrape(args.max_pages, args.sleep)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M")
    out = args.output_dir / f"bienesonline_{stamp}.geojson"
    envelope = {
        "type": "FeatureCollection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_count": len(feats),
        "features": feats,
    }
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"OK bienesonline: {len(feats)} listings → {out}")


if __name__ == "__main__":
    sys.exit(main())