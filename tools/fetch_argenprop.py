#!/usr/bin/env python3
"""tools/fetch_argenprop.py

Scraper for Argenprop (Argentine regional aggregator that includes a
modest set of Paraguay listings via /inmuebles/venta/paraguay).

This is best-effort because the endpoint gates at the Cloudflare perimeter.
When the same fetch runs against /inmuebles/venta/<prov> (Argentina) it
returns 202 with an empty body — the verification path.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

FX_PYG_PER_USD = 7_500.0
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
UA = USER_AGENT

PY_BBOX = {"lon_min": -63.5, "lon_max": -54.0, "lat_min": -27.5, "lat_max": -19.0}


def _fetch(url: str, timeout: int = 25) -> str:
    """Fetch URL with gzip/deflate support — Argenprop returns gzipped HTML."""
    import gzip
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-AR,es;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            return gzip.decompress(raw).decode("utf-8", errors="ignore")
        return raw.decode("utf-8", errors="ignore")


def _in_py(coord: list) -> bool:
    """Check coords are inside Paraguay's bounding box."""
    if not isinstance(coord, list) or len(coord) < 2:
        return False
    lon, lat = coord[0], coord[1]
    if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
        return False
    return (PY_BBOX["lon_min"] <= lon <= PY_BBOX["lon_max"]
            and PY_BBOX["lat_min"] <= lat <= PY_BBOX["lat_max"])


def _parse_argenprop_record(blob: dict, source_url: str) -> dict | None:
    """Convert an Argenprop ld+json record into our canonical feature shape."""
    sid = blob.get("@id") or blob.get("url") or source_url
    name = blob.get("name", "")
    desc = blob.get("description", "")

    geo = blob.get("geo") or {}
    lat = geo.get("latitude")
    lon = geo.get("longitude")
    if lat is None or lon is None:
        return None
    try:
        lat = float(lat); lon = float(lon)
    except (TypeError, ValueError):
        return None
    if not _in_py([lon, lat]):
        return None

    offers = blob.get("offers") or {}
    price_str = offers.get("price")
    price_curr = offers.get("priceCurrency", "USD")
    if price_str is None:
        return None
    try:
        price = float(str(price_str).replace(".", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    if price_curr.upper() == "PYG":
        price_pyg = int(price)
        price_usd = price / FX_PYG_PER_USD
    elif price_curr.upper() == "USD":
        price_usd = price
        price_pyg = price * FX_PYG_PER_USD
    else:
        return None

    address = blob.get("address") or {}
    city = address.get("addressLocality")
    state = address.get("addressRegion")
    country = address.get("addressCountry", "Paraguay")

    h = hashlib.sha1(("argenprop:" + str(sid)).encode()).hexdigest()[:12]
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "id": "ap_" + h,
            "source": "argenprop",
            "source_id": str(sid)[:64],
            "source_url": source_url,
            "source_platform": "argenprop.com",
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "title": (name or desc)[:200],
            "city": city,
            "state_province": state,
            "country": country,
            "listing_type": "sale",
            "property_type": "unknown",
            "currency": price_curr,
            "price_pyg": int(price_pyg),
            "price_usd": round(price_usd, 2),
            "bedrooms": None,
            "bathrooms": None,
            "area_sqm": None,
            "area_ha": None,
            "images": blob.get("image", [])[:8] if isinstance(blob.get("image"), list) else
                      ([blob.get("image")] if blob.get("image") else []),
            "description": (desc or "")[:1500],
            "lat": lat,
            "lon": lon,
        },
    }


def scrape_argenprop(timeout: int = 25, max_pages: int = 10) -> list[dict]:
    """Hit argenprop.com/inmuebles/<op>/paraguay across operations + pages.

    Returns a list of dict features in our canonical shape.
    """
    feats: list[dict] = []
    seen: set[str] = set()
    for op in ("venta", "alquiler"):
        for page in range(1, max_pages + 1):
            sep = "?"
            url = f"https://www.argenprop.com/inmuebles/{op}/paraguay"
            if page > 1:
                url += f"{sep}pagina={page}"
            try:
                html = _fetch(url, timeout)
            except Exception as exc:
                print(f"  warn {url}: {exc}", file=sys.stderr)
                continue
            if not html or len(html) < 5000:
                break
            # Find listing URLs in this page
            urls = re.findall(r'/([\w\-á-úñ]+--\d+)', html)
            urls = [u for u in urls if "paraguay" in u.lower() or "--" in u]
            # Argenprop pattern: <slug>--<id>  ; canonical url is /<slug>--<id>
            page_kept = 0
            for slug_id in urls:
                detail_url = "https://www.argenprop.com/" + slug_id
                if detail_url in seen:
                    continue
                seen.add(detail_url)
                # Extract basic info from the LISTING CARD directly
                # (no need to fetch every detail — Argenprop cards carry
                # most fields incl. price + address + lat/lon placeholder)
                # Try to find a JSON blob or price in the card
                # Find card by looking for "title=" or aria-label
                m_card = re.search(
                    r'<a[^>]+href="/' + re.escape(slug_id) + r'"[^>]*>(.*?)</a>',
                    html, re.DOTALL,
                )
                if not m_card:
                    continue
                card_html = m_card.group(1)
                # Find price in card
                m_price = re.search(r'\$\s*([\d.,]+)', card_html)
                if not m_price:
                    m_price = re.search(r'U\$\$?\s*([\d.,]+)', card_html)
                if not m_price:
                    continue
                try:
                    price = float(m_price.group(1).replace(".", "").replace(",", "."))
                except Exception:
                    continue
                # Currency default USD for Argenprop Paraguay
                price_usd = price
                price_pyg = int(price_usd * FX_PYG_PER_USD)
                # Find location
                city_match = re.search(r'addressLocality"?\s*[:=]\s*"?([\w\s\-]+?)[",<]', card_html)
                m_loc = re.search(r'addressRegion"?\s*[:=]\s*"?([\w\s\-]+?)[",<]', card_html)
                city = (city_match.group(1).strip() if city_match else None)
                state = (m_loc.group(1).strip() if m_loc else None)
                # Title
                title_match = re.search(r'"name":"([^"]+)"', card_html) or re.search(r'<img[^>]+alt="([^"]+)"', card_html)
                title = (title_match.group(1) if title_match else slug_id.replace("-", " ").title())[:200]
                # No lat/lon available — skip (we already drop without coords)
                # We can optionally set lat=-23.4 lon=-58.3 as a placeholder for "Other Localities Paraguay"
                # but better to skip and rely on the slug containing the dept info
                if "Otras Localidades" in title or "otras-localidades" in slug_id.lower():
                    # Use approximate centroid of Paraguay
                    lat, lon = -23.4, -58.3
                else:
                    # Fall back: try to extract from URL slug (no coords)
                    continue  # skip — we don't have coords and the listing_type is unknown

                h = hashlib.sha1(("argenprop:" + slug_id).encode()).hexdigest()[:12]
                feats.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "id": "ap_" + h,
                        "source": "argenprop",
                        "source_id": slug_id[:64],
                        "source_url": detail_url,
                        "source_platform": "argenprop.com",
                        "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
                        "title": title,
                        "city": city,
                        "state_province": state,
                        "country": "Paraguay",
                        "listing_type": op if op in ("venta", "alquiler") else "sale",
                        "property_type": "unknown",
                        "currency": "USD",
                        "price_pyg": price_pyg,
                        "price_usd": round(price_usd, 2),
                        "bedrooms": None,
                        "bathrooms": None,
                        "area_sqm": None,
                        "area_ha": None,
                        "images": [],
                        "description": "",
                        "lat": lat,
                        "lon": lon,
                    },
                })
                page_kept += 1
            print(f"  argenprop/{op} page {page}: {len(urls)} listings → kept {page_kept}")
            if page_kept == 0 and page > 1:
                break
    return feats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path,
                    default=ROOT / "data/properties/snapshots")
    ap.add_argument("--no-fetch", action="store_true",
                    help="skip network (CI mode)")
    args = ap.parse_args(argv)

    if args.no_fetch:
        feats = []
    else:
        feats = scrape_argenprop()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M")
    out = args.output_dir / f"argenprop_{stamp}.geojson"
    envelope = {
        "type": "FeatureCollection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_count": len(feats),
        "features": feats,
    }
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"OK argenprop: {len(feats)} listings → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())