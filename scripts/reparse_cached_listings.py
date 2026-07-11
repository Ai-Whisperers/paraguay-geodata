#!/usr/bin/env python3
"""scripts/reparse_cached_listings.py — re-process ALL cached detail pages with the
improved parser (price/title/depto/bedrooms), dedupe by id, and overwrite the public GeoJSON.

This is the "bulk" version of fetch_properties that doesn't hit the network. It
assumes the cache is fresh enough (last 6h is the default).
"""
import json
import hashlib
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

# Reuse the parser helpers
sys.path.insert(0, '/root/paraguay-geodata')
from tools.fetch_properties import (
    _extract_price, _extract_title, _extract_address, _extract_bedrooms,
    _extract_depto_from_url, _extract_lat_lon, _extract_area_ha,
)


def id_for_url(url: str) -> str:
    # Matches tools/fetch_properties.py id computation
    # (we don't have source_id here, so derive from URL hash)
    return "ic_" + hashlib.sha1(("infocasas:" + url).encode()).hexdigest()[:12]


def main() -> int:
    cache_dir = Path("/root/paraguay-geodata/data/properties/cache/infocasas")
    out_path = Path("/root/paraguay-geodata/exports/web/data/properties_latest.geojson")

    # Map id → best record (keep the one with most fields populated)
    best = {}
    n = 0
    for f in sorted(cache_dir.glob("*.html")):
        html = f.read_text(errors="replace")
        # Look for the source URL: usually in <link rel="canonical"> or <meta property="og:url">
        url = None
        m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        if m:
            url = m.group(1)
        else:
            m = re.search(r'<meta property="og:url" content="([^"]+)"', html)
            if m:
                url = m.group(1)
        if not url:
            continue
        # Scrape id from URL — infocasas URLs end with /<source_id>
        m = re.search(r'/(\d+)/?$', url)
        source_id = m.group(1) if m else None

        lat_lon = _extract_lat_lon(html)
        price = _extract_price(html)
        area_ha = _extract_area_ha(html)
        title = _extract_title(html)
        address = _extract_address(html)
        bedrooms = _extract_bedrooms(html)
        depto = address.get("state") if address else None
        depto_from_url = _extract_depto_from_url(url)
        if not depto:
            depto = depto_from_url
        elif depto_from_url and depto_from_url not in depto:
            depto = f"{depto} / {depto_from_url}"

        rec = {
            "id": "ic_" + (hashlib.sha1(("infocasas:" + (source_id or url)).encode()).hexdigest()[:12] if source_id else hashlib.sha1(("infocasas:" + url).encode()).hexdigest()[:12]),
            "source": "infocasas",
            "source_id": source_id,
            "source_url": url,
            "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
            "lat": round(lat_lon[0], 3) if lat_lon and lat_lon[0] else None,
            "lon": round(lat_lon[1], 3) if lat_lon and lat_lon[1] else None,
            "title": title,
            "address": address,
            "depto": depto,
            "bedrooms": bedrooms,
            "price_pyg": price["pyg"] if price else None,
            "price_usd": price["usd"] if price else None,
            "area_ha": area_ha,
            "$/ha": (price["usd"] / area_ha) if (price and area_ha and area_ha > 0) else None,
            "attrs": None,
        }
        # dedupe: prefer the one with MORE fields filled
        existing = best.get(rec["id"])
        if existing is None or sum(1 for v in rec.values() if v) > sum(1 for v in existing.values() if v):
            best[rec["id"]] = rec
        n += 1

    features = []
    for r in best.values():
        if r.get("lat") is None or r.get("lon") is None:
            continue
        # strip lat/lon from props (they live in geometry)
        rec = {k: v for k, v in r.items() if k not in ("lat", "lon")}
        feat = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": rec,
        }
        features.append(feat)

    out = {"type": "FeatureCollection", "features": features}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Reprocessed {n} cached HTML files → {len(features)} deduped listings")
    print(f"  with title:       {sum(1 for f in features if f['properties'].get('title'))}")
    print(f"  with price_usd:   {sum(1 for f in features if f['properties'].get('price_usd'))}")
    print(f"  with depto:       {sum(1 for f in features if f['properties'].get('depto'))}")
    print(f"  with bedrooms:    {sum(1 for f in features if f['properties'].get('bedrooms'))}")
    print(f"  with $/ha:        {sum(1 for f in features if f['properties'].get('$/ha'))}")
    print(f"  wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())