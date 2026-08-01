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
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-AR,es;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


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


def scrape_argenprop(timeout: int = 25) -> list[dict]:
    """Hit argenprop.com/inmuebles/venta/paraguay + extract listings.

    Note: argenprop typically gates this at Cloudflare.  When the page
    returns 202 with an empty body we return [].
    """
    url = "https://www.argenprop.com/inmuebles/venta/paraguay"
    try:
        html = _fetch(url, timeout)
    except Exception as exc:
        print(f"  warn: {url}: {exc}", file=sys.stderr)
        return []
    if not html or len(html) < 2000:
        # Cloudflare-blocked (202 + body b''), or 503
        print("  warn: argenprop response too small (likely Cloudflare block)", file=sys.stderr)
        return []

    feats: list[dict] = []
    seen_urls: set[str] = set()

    # Strategy A: ld+json ItemList
    ldj_blocks = re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL,
    )
    for blob in ldj_blocks:
        try:
            d = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if isinstance(d, dict) and d.get("@type") in ("ItemPage", "WebPage", "CollectionPage"):
            me = d.get("mainEntity") or {}
            if isinstance(me, dict) and me.get("@type") == "ItemList":
                for elem in me.get("itemListElement") or []:
                    item = elem.get("item") if isinstance(elem, dict) else None
                    if isinstance(item, dict) and item.get("url"):
                        if item["url"] in seen_urls:
                            continue
                        seen_urls.add(item["url"])
                        feat = _parse_argenprop_record(item, item["url"])
                        if feat is not None:
                            feats.append(feat)
            elif isinstance(me, dict) and me.get("geo"):
                # direct place
                if me.get("@id") in seen_urls:
                    continue
                seen_urls.add(me.get("@id", ""))
                feat = _parse_argenprop_record(me, me.get("@id") or url)
                if feat is not None:
                    feats.append(feat)
        elif isinstance(d, dict) and d.get("@type") in (
            "SingleFamilyResidence", "Apartment", "House",
            "Residence", "Place", "ApartmentComplex",
            "Product",
        ):
            if d.get("url") in seen_urls:
                continue
            seen_urls.add(d.get("url", ""))
            feat = _parse_argenprop_record(d, d.get("url") or url)
            if feat is not None:
                feats.append(feat)

    # Strategy B: href link pattern /<slug>--<id>
    listing_urls = re.findall(r'href="(/[\w\-á-úñÑÁÉÍÓÚÜ]+--\d+)"', html)
    for slug_id in listing_urls:
        detail_url = "https://www.argenprop.com" + slug_id
        if detail_url in seen_urls:
            continue
        seen_urls.add(detail_url)
        # Fetch detail page (best-effort — may fail)
        try:
            d_html = _fetch(detail_url, timeout)
        except Exception:
            continue
        for blob in re.findall(
            r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
            d_html, re.DOTALL,
        ):
            try:
                d = json.loads(blob)
            except json.JSONDecodeError:
                continue
            if isinstance(d, dict):
                feat = _parse_argenprop_record(d, detail_url)
                if feat is not None:
                    feats.append(feat)
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