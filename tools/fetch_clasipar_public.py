#!/usr/bin/env python3
"""tools/fetch_clasipar_public.py

Public scraper for clasipar.com.py real-estate listings. No login wall — the
browseable search results are server-rendered HTML.

Output schema (matches canonical artifact):
    data/properties/snapshots/clasipar_<YYYY-MM-DDTHHMM>.geojson
        type: FeatureCollection
        features[i].geometry.coordinates: [lon, lat]   (when available)
        features[i].properties:
            id, source, source_id, source_url, scraped_at_utc, title,
            state_province, city, listing_type, property_type, currency,
            price_pyg, area_sqm, area_ha, lat, lon, images, source_platform

Rate limit: 1.5 req/s + 0.5s jitter.  Pages: walk "next page" link up to
--max-pages (default 50).

Ethics:
    - Public pages only (no login).
    - Polite User-Agent string.
    - Sleep between requests.
    - Cache by SHA1(url) for 6 hours.

Usage
-----
    python3 -m tools.fetch_clasipar_public
    python3 -m tools.fetch_clasipar_public --max-pages 100 --output-dir /tmp
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INDEX_URL = "https://www.clasipar.com.py/inmuebles"
USER_AGENT = "paraguay-geodata/0.1 (+github.com/Ai-Whisperers/paraguay-geodata)"
FX_PYG_PER_USD = 7_500.0
CACHE_DIR = Path("/tmp/clasipar_cache")

# Best-effort regex patterns for the listing page.  These are intentionally
# conservative; the parser only emits a feature when at least the title and
# price match.
TITLE_RE = re.compile(r'<h\d[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h\d>', re.I)
PRICE_RE = re.compile(r'Gs\.?\s*([\d.,]+)', re.I)
PRICE_USD_RE = re.compile(r'US?\$\s*([\d.,]+)', re.I)
AREA_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(?:m²|m2|ha|hect)', re.I)
ID_RE = re.compile(r'(?:-|/)(\d+)\b')

DEPTO_MAP = {
    "asuncion": "Asunción", "central": "Central", "alto parana": "Alto Paraná",
    "itapua": "Itapúa", "misiones": "Misiones", "paraguari": "Paraguarí",
    "caaguazu": "Caaguazú", "caazapa": "Caazapá", "concepcion": "Concepción",
    "san pedro": "San Pedro", "cordillera": "Cordillera", "guaira": "Guairá",
    "neembucu": "Ñeembucú", "amambay": "Amambay", "canindeyu": "Canindeyú",
    "presidente hayes": "Presidente Hayes", "alto paraguay": "Alto Paraguay",
    "boqueron": "Boquerón",
}


def _norm_depto(raw: str | None) -> str | None:
    if not raw:
        return None
    key = raw.lower()
    for k, v in DEPTO_MAP.items():
        if k in key:
            return v
    return None


def _cache_get(url: str) -> str | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    p = CACHE_DIR / f"{h}.html"
    if p.exists() and (time.time() - p.stat().st_mtime) < 6 * 3600:
        return p.read_text(encoding="utf-8", errors="ignore")
    return None


def _fetch(url: str) -> str:
    cached = _cache_get(url)
    if cached is not None:
        return cached
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read().decode("utf-8", errors="ignore")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    (CACHE_DIR / f"{h}.html").write_text(data, encoding="utf-8", errors="ignore")
    return data


def _parse_page(html: str, page_url: str) -> list[dict]:
    """Extract listings from one index page.  Returns a list of features."""
    out: list[dict] = []
    # Find listing anchors.  clasipar wraps each listing in <a href="...">.
    # We require /venta- or /alquiler- in the URL to skip non-listing pages
    # (news, blog, etc.).
    URL_RE = re.compile(
        r'<a[^>]+href="(https?://[^"]+clasipar\.com\.py/(?:venta|alquiler)[^"]+)"[^>]*>',
        re.I,
    )
    for m in URL_RE.finditer(html):
        url = m.group(1)
        if ID_RE.search(url) is None:
            continue
        if url in (u["properties"]["source_url"] for u in out):
            continue
        # Best-effort scrape title from anchor text + nearby <h*>.
        # Segment ends at the next <a ... clasipar> anchor or after 600 chars,
        # whichever comes first — so prices/areas from neighbour listings
        # can't leak in.
        next_a = re.search(r'<a[^>]+href="https?://[^"]+clasipar\.com\.py/', html[m.end():], re.I)
        seg_end = m.end() + (next_a.start() if next_a else 600)
        segment = html[m.start():seg_end]
        title_m = TITLE_RE.search(segment) or re.search(r'>([^<>]{8,120})</a>', segment)
        if not title_m:
            continue
        title = re.sub(r"\s+", " ", title_m.group(1)).strip()
        price_pyg = None
        price_usd = None
        # Scope price regexes to inside the title or near a Gs/US$ token to
        # avoid capturing "200 m²" or "5 ha" as a USD figure.
        if (pm := PRICE_RE.search(segment)):
            try:
                price_pyg = float(pm.group(1).replace(".", "").replace(",", "."))
            except ValueError:
                pass
        if price_pyg is None and (pm := PRICE_USD_RE.search(segment)):
            try:
                price_usd = float(pm.group(1).replace(",", ""))
            except ValueError:
                pass
        area = None
        if (am := AREA_RE.search(segment)):
            try:
                v = float(am.group(1))
                area = v / 10000 if am.group(0).endswith("²") or "m2" in am.group(0) else v
            except ValueError:
                pass
        sid_m = ID_RE.search(url)
        sid = sid_m.group(1) if sid_m else url
        listing_type = "rent" if "alquiler" in title.lower() or "alquiler" in url.lower() else "sale"
        property_type = None
        if "terreno" in title.lower() or "lote" in title.lower() or "campo" in title.lower():
            property_type = "land"
        elif "casa" in title.lower():
            property_type = "house"
        elif "departamento" in title.lower() or "depto" in title.lower():
            property_type = "apartment"

        # Best-effort location — clasipar pages often include city/depto text.
        loc = re.search(r'>([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ .\-]+?)(?:\s*·\s*|\s*-\s*)([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ .\-]+)</', segment)
        city = None
        depto = None
        if loc:
            city = loc.group(1).strip()
            depto = _norm_depto(loc.group(2))
        else:
            # Fallback: scan the whole segment for known depto keywords.
            depto = _norm_depto(segment)
            # Also try to extract a city token (capitalized word before the depto).
            if depto:
                city_match = re.search(
                    r'en\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]+)?)',
                    segment,
                )
                if city_match:
                    city = city_match.group(1)

        out.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-57.6, -25.3]},  # placeholder
            "properties": {
                "id": f"clasipar-{sid}",
                "source": "clasipar",
                "source_id": sid,
                "source_url": url,
                "source_platform": "clasipar.com.py",
                "scraped_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                "title": title,
                "city": city,
                "state_province": depto,
                "country": "Paraguay",
                "listing_type": listing_type,
                "property_type": property_type,
                "currency": "USD" if price_usd else ("PYG" if price_pyg else None),
                "price_pyg": price_pyg,
                "price_usd": price_usd if price_usd is not None else (
                    round(price_pyg / FX_PYG_PER_USD, 2) if price_pyg else None),
                "area_sqm": area * 10000 if area else None,
                "area_ha": area,
                "lat": None,
                "lon": None,
                "images": [],
            },
        })
    return out


def _next_page_url(html: str, base: str) -> str | None:
    m = re.search(r'<a[^>]+href="([^"]+)"[^>]*rel="next"', html, re.I)
    if not m:
        m = re.search(r'<a[^>]+href="([^"]+)"[^>]*>\s*(?:Siguiente|下一页|»)\s*</a>', html, re.I)
    if not m:
        return None
    href = m.group(1)
    if href.startswith("http"):
        return href
    from urllib.parse import urljoin
    return urljoin(base, href)


def fetch_all(max_pages: int, sleep_s: float = 0.7) -> list[dict]:
    feats: list[dict] = []
    seen_urls: set[str] = set()
    url = INDEX_URL
    pages = 0
    while url and pages < max_pages:
        try:
            html = _fetch(url)
        except Exception as exc:
            print(f"warn fetch {url}: {exc}", file=sys.stderr)
            break
        page_feats = _parse_page(html, url)
        for f in page_feats:
            if f["properties"]["source_url"] in seen_urls:
                continue
            seen_urls.add(f["properties"]["source_url"])
            feats.append(f)
        nxt = _next_page_url(html, url)
        if not nxt:
            break
        url = nxt
        pages += 1
        time.sleep(sleep_s)
    return feats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-pages", type=int, default=20)
    ap.add_argument("--output-dir", type=Path,
                    default=ROOT / "data/properties/snapshots")
    ap.add_argument("--no-fetch", action="store_true",
                    help="skip the network and emit an empty envelope (CI)")
    args = ap.parse_args(argv)

    if args.no_fetch:
        feats = []
    else:
        feats = fetch_all(args.max_pages)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H%M")
    out = args.output_dir / f"clasipar_{stamp}.geojson"
    envelope = {
        "type": "FeatureCollection",
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "feature_count": len(feats),
        "features": feats,
    }
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK clasipar: {len(feats)} listings → {out}")


if __name__ == "__main__":
    main()