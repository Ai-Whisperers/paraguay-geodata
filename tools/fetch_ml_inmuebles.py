#!/usr/bin/env python3
"""tools/fetch_ml_inmuebles.py

Scraper for MercadoLibre Paraguay Inmuebles catalog (https://inmuebles.mercadolibre.com.py/).

The catalog pages include polycards with the listing URL + key facts even
when the broader site gates account verification.  Pulling the catalog
HTML yields ~30-80 listings per page (casa/venta, terreno/venta,
departamento/venta, casa/alquiler).

Strategy:
  1. Hit the catalog URL → extract polycard titles, prices, area_covered,
     bedrooms + the /p/MLA-XXXXX permalink.
  2. For each distinct permalink, attempt to GET the listing detail (public
     pages work without an account; the gating only affects commenting).
  3. Detail pages have ld+json with the full record.

Note: Even when the catalog is gated (Cloudflare), the link extraction
works because the rendered HTML still embeds the search-result JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FX_PYG_PER_USD = 7_500.0
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
UA = USER_AGENT
PY_BBOX = {"lon_min": -63.5, "lon_max": -54.0, "lat_min": -27.5, "lat_max": -19.0}

CATALOG_PATHS = [
    "/casa/venta",
    "/departamento/venta",
    "/terreno/venta",
    "/casa/alquiler",
    "/departamento/alquiler",
    "/terreno/alquiler",
    "/local/venta",
    "/oficina/venta",
]


def _fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-PY,es;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def _in_py(lon, lat) -> bool:
    return (PY_BBOX["lon_min"] <= lon <= PY_BBOX["lon_max"]
            and PY_BBOX["lat_min"] <= lat <= PY_BBOX["lat_max"])


def _parse_polycard(item: dict, source_url: str) -> dict | None:
    """Build a record from a MercadoLibre polycard.

    polycards carry: id, title, price (with .currency in /price/ sub-obj),
    attributes (covered_area, bedrooms, full_bathrooms), permalink, plus
    lat/lon (when the listing has a precise location).
    """
    sid = item.get("id") or item.get("permalink") or item.get("title")
    if not sid:
        return None
    title = item.get("title", "")
    permalink = item.get("permalink", "")

    price_obj = item.get("price") or {}
    amount = price_obj.get("amount") if isinstance(price_obj, dict) else price_obj
    currency = (price_obj.get("currency_id") if isinstance(price_obj, dict)
                else price_obj.get("currency") if isinstance(price_obj, dict) else None) or "PYG"
    if amount is None:
        return None
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return None
    if currency == "PYG":
        price_pyg = int(amount)
        price_usd = amount / FX_PYG_PER_USD
    elif currency == "USD":
        price_usd = amount
        price_pyg = amount * FX_PYG_PER_USD
    else:
        return None

    attrs = item.get("attributes") or []
    attr_dict = {}
    for a in attrs:
        if isinstance(a, dict) and "name" in a and "value_name" in a:
            attr_dict[a["name"]] = a["value_name"]
    area_str = attr_dict.get("COVERED_AREA") or attr_dict.get("AREA") or attr_dict.get("TOTAL_AREA")
    area_sqm = None
    if area_str:
        m = re.search(r"(\d+(?:[.,]\d+)?)", str(area_str))
        if m:
            area_sqm = float(m.group(1).replace(",", "."))
            if area_str and "m²" not in str(area_str) and "mts" not in str(area_str) and "ha" in str(area_str).lower():
                area_sqm *= 10000  # hectares was reported

    bedrooms = None
    bdr = attr_dict.get("BEDROOMS") or attr_dict.get("DORMITORIOS")
    if bdr:
        bm = re.search(r"\d+", str(bdr))
        if bm:
            bedrooms = int(bm.group())
    bathrooms = None
    bth = attr_dict.get("FULL_BATHROOMS") or attr_dict.get("BATHROOMS")
    if bth:
        bm = re.search(r"\d+", str(bth))
        if bm:
            bathrooms = int(bm.group())

    lat = item.get("location", {}).get("latitude") if isinstance(item.get("location"), dict) else None
    lon = item.get("location", {}).get("longitude") if isinstance(item.get("location"), dict) else None
    if lat is None or lon is None:
        # Many ML listings don't have coords. Skip — we'll add via detail page later.
        return None
    try:
        lat = float(lat); lon = float(lon)
    except (TypeError, ValueError):
        return None
    if not _in_py(lon, lat):
        return None

    city = item.get("city") or item.get("address", {}).get("city_name") if isinstance(item.get("address"), dict) else None
    state = item.get("state") or item.get("address", {}).get("state_name") if isinstance(item.get("address"), dict) else None

    h = hashlib.sha1(("mlpy:" + str(sid)).encode()).hexdigest()[:12]
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "id": "ml_" + h,
            "source": "mercadolibre",
            "source_id": str(sid)[:64],
            "source_url": permalink or source_url,
            "source_platform": "mercadolibre.com.py",
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "title": title[:200],
            "city": city,
            "state_province": state,
            "country": "Paraguay",
            "listing_type": "sale",
            "property_type": _map_property_type(title),
            "currency": currency,
            "price_pyg": price_pyg,
            "price_usd": round(price_usd, 2),
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "area_sqm": area_sqm,
            "area_ha": round(area_sqm / 10000, 4) if area_sqm else None,
            "images": (item.get("pictures") or [])[:8],
            "description": "",
            "lat": lat,
            "lon": lon,
        },
    }


def _map_property_type(title: str) -> str:
    t = (title or "").lower()
    if "departamento" in t or "apartment" in t: return "apartment"
    if "casa" in t or "chalet" in t: return "house"
    if "terreno" in t or "lote" in t: return "land"
    if "quinta" in t: return "house"
    if "oficina" in t: return "commercial"
    if "local" in t or "galpón" in t or "galpon" in t or "deposito" in t or "depósito" in t: return "commercial"
    if "estancia" in t or "campo" in t or "finca" in t: return "land"
    return "unknown"


def scrape_catalog_paths(paths: list[str], max_pages: int, sleep_s: float) -> list[dict]:
    base = "https://inmuebles.mercadolibre.com.py"
    feats: list[dict] = []
    seen: set[str] = set()
    import time
    for path in paths:
        for page in range(1, max_pages + 1):
            offset = (page - 1) * 48 + 1  # MercadoLibre uses _Desde_ for pagination
            url = f"{base}{path}"
            if page > 1:
                sep = "&" if "?" in path else "?"
                # ML PY uses ?_Desde_ offset
                url += f"{sep}_Desde_{offset}"
            try:
                html = _fetch(url, 12)
            except Exception as exc:
                print(f"  warn {url}: {exc}", file=sys.stderr)
                break
            if not html or len(html) < 2000:
                print(f"  {path} page {page}: no body", file=sys.stderr)
                break
            # Find polycard JSON
            # Pattern A: window.__PRELOADED_STATE__
            chunks = re.findall(r'"results":\s*(\[\{.*?\}\])', html, re.DOTALL)
            if chunks:
                import json as _json
                try:
                    arr = _json.loads(chunks[0])
                except Exception:
                    arr = []
            else:
                arr = []
            # Pattern B: inline json-state polycards
            if not arr:
                # look for "polycard" entries inside window.__ML__.catalog_state
                # fallback: just look for any "id" => MLA-style
                items = re.findall(r'\{\\?"id\\?":\\?"(ML[A-Z]\-\d{6,15})\\?"', html)
                arr = [{"id": i, "title": "(via polycard)", "permalink": f"https://articulo.mercadolibre.com.py/{i}-_JM"} for i in items]

            page_kept = 0
            for item in arr:
                feat = _parse_polycard(item, url)
                if feat is None:
                    continue
                key = feat["properties"]["source_url"]
                if key in seen:
                    continue
                seen.add(key)
                feats.append(feat)
                page_kept += 1
            print(f"  {path} page {page}: {len(arr)} polycards → kept {page_kept}")
            if page_kept == 0 and page > 1:
                break
            time.sleep(sleep_s)
    return feats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paths", nargs="+", default=CATALOG_PATHS)
    ap.add_argument("--max-pages", type=int, default=3)
    ap.add_argument("--sleep", type=float, default=0.7)
    ap.add_argument("--output-dir", type=Path,
                    default=ROOT / "data/properties/snapshots")
    ap.add_argument("--no-fetch", action="store_true")
    args = ap.parse_args(argv)

    if args.no_fetch:
        feats = []
    else:
        feats = scrape_catalog_paths(args.paths, args.max_pages, args.sleep)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M")
    out = args.output_dir / f"mercadolibre_{stamp}.geojson"
    envelope = {
        "type": "FeatureCollection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feature_count": len(feats),
        "features": feats,
    }
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"OK mercadolibre: {len(feats)} listings → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())