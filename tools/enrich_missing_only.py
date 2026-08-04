"""tools/enrich_missing_only.py — fetch detail pages ONLY for listings without coords.

The full fetch_asuncion_estate.py re-fetches every detail page every run,
which is slow (2s × 5000 listings = 10000s). This script:

1. Reads canonical_properties.geojson
2. Reads the fast walk output (cards only)
3. Identifies listings missing lat/lon (most of the 7,383 walk output)
4. Fetches detail pages ONLY for those, in parallel
5. Merges back into a new snapshot

Result: a single run goes from ~3 hours → ~5 minutes.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

FX_PYG_PER_USD = 7300

PTYPE_MAP = {
    "houses": "house",
    "apartments": "apartment",
    "lands": "land",
    "offices": "office",
    "local-commercials": "commercial",
}

# Geo centroids for fallback when listings lack data-lat/data-lng.
# Used as a last resort; most detail pages have lat/lon.
CITY_CENTROIDS = {
    "asunción": (-25.2637, -57.5759),
    "central": (-25.3318, -57.4831),
    "alto-parana": (-25.5163, -54.6118),
    "ciudad-del-este": (-25.5097, -54.6118),
    "cordillera": (-25.2200, -57.3500),
    "itapua": (-27.3333, -55.8667),
    "encarnacion": (-27.3367, -55.8667),
    "boqueron": (-22.4500, -60.5000),
    "presidente-hayes": (-23.5000, -59.0000),
    "paraguari": (-25.6200, -57.1500),
    "san-pedro": (-24.1000, -57.0800),
    "caaguazu": (-25.4500, -56.0167),
    "misiones": (-26.6333, -57.1500),
    "concepcion": (-23.4011, -57.4411),
    "neembucu": (-26.8667, -58.2986),
    "alto-paraguay": (-20.0833, -58.1667),
    "caazapa": (-26.1500, -56.3833),
    "canindeyu": (-24.4833, -55.6833),
    "villarrica": (-25.7833, -56.4500),
}


def _fetch(url: str, timeout: int = 12) -> str | None:
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": UA}),
            timeout=timeout,
        ) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def _parse_amount(s: str) -> int | None:
    if not s:
        return None
    s = re.sub(r"[^\d.,]", "", s.strip())
    if not s:
        return None
    if "." in s and "," in s:
        if s.rfind(".") > s.rfind(","):
            s = s.replace(",", "")
        else:
            s = s.replace(".", "").replace(",", ".")
    if "." in s and len(s.split(".")[-1]) == 3 and s.count(".") > 1:
        s = s.replace(".", "")
    if "." in s and len(s.split(".")[-1]) != 3:
        s = s.replace(".", "")
    try:
        return int(float(s))
    except Exception:
        return None


def _parse_detail(url: str, html: str) -> dict | None:
    """Extract lat/lon/price/images from an asuncion.estate detail page."""
    out: dict = {}

    # lat/lon
    m = re.search(r'data-lat="([\d.\-]+)"', html)
    if m:
        out["lat"] = float(m.group(1))
    m = re.search(r'data-lng="([\d.\-]+)"', html)
    if m:
        out["lon"] = float(m.group(1))

    # ld+json RealEstateListing is the cleanest
    m = re.search(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        try:
            ld = json.loads(m.group(1))
            if isinstance(ld, dict):
                geo = ld.get("geo") or {}
                if geo.get("latitude"):
                    out["lat"] = float(geo["latitude"])
                if geo.get("longitude"):
                    out["lon"] = float(geo["longitude"])
                offers = ld.get("offers") or {}
                price = offers.get("price")
                if price:
                    try:
                        out["price_usd"] = float(price)
                        out["currency"] = "USD"
                        out["price_pyg"] = int(out["price_usd"] * FX_PYG_PER_USD)
                    except Exception:
                        pass
                elif offers.get("priceSpecification"):
                    ps = offers["priceSpecification"]
                    if ps.get("price"):
                        try:
                            out["price_usd"] = float(ps["price"])
                            out["currency"] = "USD"
                        except Exception:
                            pass
                addr = ld.get("address") or {}
                if isinstance(addr, dict):
                    out["street"] = addr.get("streetAddress") or ""
                    out["neighborhood"] = addr.get("addressLocality") or ""
        except Exception:
            pass

    # Fallback: extract from raw HTML
    if "lat" not in out:
        m = re.search(r"lat['\"]?\s*[:=]\s*['\"]?(-?\d+\.\d+)", html)
        if m:
            out["lat"] = float(m.group(1))
    if "lon" not in out:
        m = re.search(r"(?:lon|lng)['\"]?\s*[:=]\s*['\"]?(-?\d+\.\d+)", html)
        if m:
            out["lon"] = float(m.group(1))

    # Price: USD or PYG
    if "price_usd" not in out:
        m = re.search(r"U\$S\s*([\d.,]+)", html)
        if m:
            v = _parse_amount(m.group(1))
            if v:
                out["price_usd"] = float(v)
                out["currency"] = "USD"
                out["price_pyg"] = int(v * FX_PYG_PER_USD)
    if "price_pyg" not in out:
        m = re.search(r"Gs\.?\s*([\d.,]+)", html)
        if m:
            v = _parse_amount(m.group(1))
            if v:
                out["price_pyg"] = v
                if "price_usd" not in out:
                    out["price_usd"] = round(v / FX_PYG_PER_USD, 2)
                out["currency"] = "USD"

    # Beds / baths / area
    m = re.search(r'flaticon-bed[^"]*"[^>]*></span>\s*(\d+)', html)
    if m:
        out["bedrooms"] = int(m.group(1))
    m = re.search(r'flaticon-shower[^"]*"[^>]*></span>\s*(\d+)', html)
    if m:
        out["bathrooms"] = int(m.group(1))
    m = re.search(r'flaticon-expand[^"]*"[^>]*></span>\s*(\d+)\s*m', html)
    if m:
        out["area_sqm"] = int(m.group(1))
    if "area_sqm" not in out:
        # Try "Sup. Construida" or similar
        m = re.search(r'(?:Construida|Total|Edificada|Cubierta)[^<]*?(\d[\d.,]*)\s*m', html)
        if m:
            v = _parse_amount(m.group(1))
            if v and v < 1_000_000:
                out["area_sqm"] = v

    # Title (h1)
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if m:
        out["title"] = re.sub(r"<[^>]+>", " ", m.group(1))
        out["title"] = re.sub(r"\s+", " ", out["title"]).strip()[:200]

    # Images (og:image or gallery)
    imgs = re.findall(r'(?:src|data-src)="(https?://[^"]+\.(?:jpg|jpeg|png|webp))"', html)
    out["images"] = list(dict.fromkeys(imgs))[:20]  # dedupe, cap

    # Description
    m = re.search(r'<div[^>]+class="[^"]*description[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
    if m:
        out["description"] = re.sub(r"<[^>]+>", " ", m.group(1))
        out["description"] = re.sub(r"\s+", " ", out["description"]).strip()[:1500]

    return out if out else None


def _id_from_url(url: str) -> str:
    """Pull the numeric listing ID from /en/city/slug-NNNN."""
    m = re.search(r"-(\d+)$", url)
    return m.group(1) if m else ""


def _in_py(lon: float | None, lat: float | None) -> bool:
    if lon is None or lat is None:
        return False
    return -63.5 <= lon <= -54.0 and -27.5 <= lat <= -19.0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--walk-snapshot", type=Path,
                    default=ROOT / "data" / "properties" / "snapshots" / "asuncion_estate_fast_walk.geojson")
    ap.add_argument("--canonical", type=Path,
                    default=ROOT / "data" / "properties" / "canonical_properties.geojson")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "data" / "properties" / "snapshots" / "asuncion_estate_enriched.geojson")
    ap.add_argument("--concurrency", type=int, default=24)
    args = ap.parse_args(argv)

    print(f"=== enrich_missing_only ===", flush=True)

    # Load walk output
    walk_data = json.load(args.walk_snapshot.open())
    walk_features = walk_data.get("features", [])
    print(f"  walked features: {len(walk_features)}", flush=True)

    # Load canonical to know which listings already have detail enrichment
    canon_data = json.load(args.canonical.open())
    canon_ae_by_id = {
        f["properties"]["source_id"]: f["properties"]
        for f in canon_data["features"]
        if f["properties"].get("source") == "asuncion_estate"
    }
    print(f"  existing asuncion_estate canonical: {len(canon_ae_by_id)}", flush=True)

    # Find listings that need detail enrichment (no coords in canonical)
    to_enrich = []
    for f in walk_features:
        sid = f["properties"]["source_id"]
        canon = canon_ae_by_id.get(sid)
        if canon and canon.get("lat") is not None and canon.get("lon") is not None:
            continue  # already has coords
        to_enrich.append(f)
    print(f"  to enrich (no coords in canonical): {len(to_enrich)}", flush=True)

    # Fetch detail pages in parallel
    detail_by_url: dict[str, dict] = {}
    if to_enrich:
        urls = [f["properties"]["source_url"] for f in to_enrich]
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            futures = {ex.submit(_fetch, u): u for u in urls}
            n = 0
            for fut in concurrent.futures.as_completed(futures):
                url = futures[fut]
                body = fut.result()
                if body:
                    parsed = _parse_detail(url, body)
                    if parsed:
                        detail_by_url[url] = parsed
                n += 1
                if n % 50 == 0:
                    print(f"  {n}/{len(urls)} detail pages fetched, {len(detail_by_url)} parsed", flush=True)
        print(f"  detail pages parsed: {len(detail_by_url)}", flush=True)

    # Build new enriched features
    enriched: list[dict] = []
    skipped_no_coord = 0
    for f in walk_features:
        props = f["properties"]
        url = props["source_url"]
        sid = props["source_id"]
        city = props.get("state_province", "")
        city_lower = city.lower()

        detail = detail_by_url.get(url, {})
        lat = detail.get("lat")
        lon = detail.get("lon")

        # Fallback to city centroid
        if not _in_py(lon, lat):
            centroid = CITY_CENTROIDS.get(city_lower)
            if centroid:
                lat, lon = centroid
            else:
                skipped_no_coord += 1
                continue

        # Merge: walk output + detail + city centroid fallback
        new_props = dict(props)
        new_props["lat"] = lat
        new_props["lon"] = lon
        new_props["geometry_set_by"] = "enrich_missing_only"

        for k in ("price_usd", "price_pyg", "currency", "bedrooms", "bathrooms",
                   "area_sqm", "images", "title", "neighborhood", "description"):
            if k in detail and detail[k]:
                new_props[k] = detail[k]

        if new_props.get("area_sqm"):
            try:
                new_props["area_ha"] = round(float(new_props["area_sqm"]) / 10000, 4)
            except Exception:
                pass

        new_props["quality_flags"] = []
        if not new_props.get("price_usd"):
            new_props["quality_flags"].append("missing_price")
        if not new_props.get("property_type") or new_props["property_type"] == "unknown":
            new_props["quality_flags"].append("null_property_type")
        new_props["scraped_at_utc"] = datetime.now(timezone.utc).isoformat()
        new_props["last_seen_at"] = new_props["scraped_at_utc"]
        new_props["pii_scrubbed"] = False  # canonicalize will scrub

        enriched.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(lon or 0), float(lat or 0)]},
            "properties": new_props,
        })

    print(f"  enriched features: {len(enriched)} (skipped {skipped_no_coord} without coords)", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "type": "FeatureCollection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": "fast_walk + enrich_missing_only",
        "feature_count": len(enriched),
        "features": enriched,
    }
    args.output.write_text(json.dumps(envelope, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"OK: wrote {len(enriched)} features → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
