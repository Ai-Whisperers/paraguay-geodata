#!/usr/bin/env python3
"""tools/merge_fresh_sources.py

Combine the freshly-fetched TuLugar snapshot with the raw infocasas depto
snapshots and emit a fresh properties_latest.geojson.  Unlike
scripts/merge_property_sources.py (which reads from properties_latest.geojson
recursively), this reads from the raw source snapshots directly.

Output:
    exports/web/data/properties_latest.geojson (FeatureCollection)
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FX_PYG_PER_USD = 7_500.0

# Fill in state_province from city when the source omitted it.  Imports the
# shared table so a single edit propagates.
sys.path.insert(0, str(ROOT / "tools"))
from _city_depto_table import depto_for_city  # noqa: E402


def _norm_infocasas(rec: dict) -> dict:
    """Convert raw infocasas scraper output → canonical feature."""
    geom = {"type": "Point", "coordinates": [rec.get("lon"), rec.get("lat")]}
    city = rec.get("city")
    state_province = rec.get("state_province") or depto_for_city(city)
    return {
        "type": "Feature",
        "geometry": geom,
        "properties": {
            "id": rec.get("id"),
            "source": "infocasas",
            "source_id": rec.get("source_id"),
            "source_url": rec.get("source_url"),
            "source_platform": "infocasas.com.py",
            "scraped_at_utc": rec.get("scraped_at_utc"),
            "title": rec.get("title"),
            "city": city,
            "neighborhood": rec.get("neighborhood"),
            "state_province": state_province,
            "country": "Paraguay",
            "listing_type": rec.get("listing_type") or "sale",
            "property_type": rec.get("property_type"),
            "currency": rec.get("currency"),
            "price_pyg": rec.get("price_pyg"),
            "price_usd": rec.get("price_usd"),
            "area_sqm": rec.get("area_sqm"),
            "area_ha": rec.get("area_ha"),
            "bedrooms": rec.get("bedrooms"),
            "bathrooms": rec.get("bathrooms"),
            "parking_spaces": rec.get("parking_spaces"),
            "images": rec.get("images") or [],
            "lat": rec.get("lat"),
            "lon": rec.get("lon"),
        },
    }


def _norm_tulugar(feat: dict) -> dict:
    """TuLugar features are already in the right schema; just ensure
    lat/lon exist and fill state_province from city when missing."""
    p = feat.get("properties") or {}
    if not p.get("state_province"):
        p["state_province"] = depto_for_city(p.get("city"))
    return feat


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--infocasas-dir", type=Path,
                    default=ROOT / "data/properties/snapshots")
    ap.add_argument("--tulugar", type=Path,
                    default=ROOT / "exports/web/data/properties_tulugar.geojson")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "exports/web/data/properties_latest.geojson")
    args = ap.parse_args(argv)

    feats: list[dict] = []

    # Strict Paraguay bounding box: real Paraguay is between lon [-63.5,-54]
    # and lat [-27.5,-19].  Anything outside is bogus geocoding (the
    # scrapers sometimes pick up the Argentina/Uruguay fallback view).
    PY_BBOX = {"lon_min": -63.5, "lon_max": -54.0, "lat_min": -27.5, "lat_max": -19.0}

    def _in_py(coord):
        if not isinstance(coord, list) or len(coord) < 2:
            return False
        lon, lat = coord[0], coord[1]
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            return False
        return (PY_BBOX["lon_min"] <= lon <= PY_BBOX["lon_max"]
                and PY_BBOX["lat_min"] <= lat <= PY_BBOX["lat_max"])

    # Raw infocasas depto snapshots
    n_ic = 0
    n_ic_dropped = 0
    if args.infocasas_dir.exists():
        for path in sorted(args.infocasas_dir.glob("*_2026-*.geojson")):
            try:
                d = json.loads(path.read_text())
            except Exception as e:
                print(f"  warn {path.name}: {e}", file=sys.stderr)
                continue
            for rec in d.get("raw_records") or []:
                if not rec.get("source_url"):
                    continue
                if not _in_py([rec.get("lon"), rec.get("lat")]):
                    n_ic_dropped += 1
                    continue
                feats.append(_norm_infocasas(rec))
                n_ic += 1

    # GeoJSON FeatureCollection snapshots from additional scrapers
    # (century21, argenprop, mercadolibre, bienesonline).  These use
    # canonical ['features'] envelopes with proper lat/lon already inside.
    extra_sources = {"century21", "argenprop", "mercadolibre", "bienesonline", "asuncion_estate"}
    n_extra = {}
    n_extra_drop = {}
    if args.infocasas_dir.exists():
        for path in sorted(args.infocasas_dir.glob("*_2026-*.geojson")):
            # Skip files already handled by the raw_records loop (they have
            # 'raw_records' or 'features'-with-ic_* ids; we only consume the
            # canonical GeoJSON envelopes now).
            try:
                d = json.loads(path.read_text())
            except Exception as e:
                continue
            if d.get("raw_records"):
                continue
            if d.get("type") != "FeatureCollection":
                continue
            for f in d.get("features") or []:
                p = f.get("properties") or {}
                src = p.get("source")
                if src not in extra_sources:
                    continue
                if not p.get("source_url"):
                    continue
                if not _in_py([
                    p.get("lon"),
                    p.get("lat"),
                ]):
                    n_extra_drop[src] = n_extra_drop.get(src, 0) + 1
                    continue
                feats.append(f)
                n_extra[src] = n_extra.get(src, 0) + 1
    for s, n in sorted(n_extra.items()):
        d = n_extra_drop.get(s, 0)
        print(f"  {s}:     {n:,}  (dropped {d} out-of-bounds)")
    print(f"  infocasas: {n_ic:,}  (dropped {n_ic_dropped} out-of-bounds)")

    # Fresh TuLugar
    n_tl = 0
    n_tl_dropped = 0
    if args.tulugar.exists():
        d = json.loads(args.tulugar.read_text())
        for f in d.get("features") or []:
            p = f.get("properties") or {}
            if p.get("lat") is None or p.get("lon") is None:
                continue
            if not _in_py([p.get("lon"), p.get("lat")]):
                n_tl_dropped += 1
                continue
            feats.append(_norm_tulugar(f))
            n_tl += 1
    print(f"  tulugar:   {n_tl:,}  (dropped {n_tl_dropped} out-of-bounds)")

    # Dedupe by source_url (keep first seen, prefer tulugar order)
    seen: dict[str, dict] = {}
    for f in feats:
        u = f["properties"]["source_url"]
        if u not in seen:
            seen[u] = f
    deduped = list(seen.values())
    print(f"  unique source_urls: {len(deduped):,}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "type": "FeatureCollection",
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "feature_count": len(deduped),
        "features": deduped,
    }
    args.output.write_text(json.dumps(envelope, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"  wrote {args.output} ({args.output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()