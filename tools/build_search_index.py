"""tools/build_search_index.py — generate small per-depto search indexes.

The full canonical_properties.geojson is 18 MB and even a slim 5.3 MB
version is too large to filter on Cloudflare Pages Functions (free tier:
100ms CPU budget).

Instead, this tool builds per-depto indexes. The biggest depto (Asunción)
is ~5,200 listings but most deptos are <500 listings each. Each per-depto
file is ~50-500 KB, well within CF Function limits.

Files written:
  exports/web/data/search/<depto-slug>.json — per-depto slim records
  exports/web/data/search/_index.json     — list of deptos + counts

A CF Pages Function at /api/v1/search reads the relevant per-depto file
based on the depto param and filters in-memory.

Usage:
  python3 -m tools.build_search_index
  python3 -m tools.build_search_index --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANON = REPO / "data" / "properties" / "canonical_properties.geojson"
OUT_DIR = REPO / "exports" / "web" / "data" / "search"


def slug(s: str) -> str:
    """Convert 'Asunción' → 'asuncion', 'Alto Paraná' → 'alto-parana'.

    Strips diacritics so accented deptos produce clean ASCII slugs that
    work in URLs without escaping.
    """
    import unicodedata
    s = unicodedata.normalize("NFKD", s)
    # Decompose accents, drop combining marks
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "unknown"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build per-depto search indexes.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not CANON.exists():
        print(f"  ERR: {CANON} not found")
        return 1

    print("=== build_search_index ===")
    data = json.loads(CANON.read_text())
    features = data.get("features", [])
    n = len(features)
    print(f"  loaded {n:,} features")

    # Group by depto
    by_depto: dict[str, list] = {}
    unassigned = []

    for f in features:
        p = f["properties"]
        coords = (f.get("geometry") or {}).get("coordinates") or [None, None]
        lon, lat = coords[0], coords[1]
        images = p.get("images") or []
        primary_image = images[0] if images else None

        def num(key, default=0):
            v = p.get(key, default)
            if v is None: return default
            try: return float(v)
            except (ValueError, TypeError): return default

        slim = {
            "id": p.get("id") or "",
            "ln": p.get("listing_number"),
            "t": (p.get("title") or "")[:120],
            "p": num("price_usd"),
            "a": num("area_ha"),
            "k": num("bedrooms"),
            "w": num("bathrooms"),
            "pt": p.get("property_type") or "",
            "c": p.get("city") or "",
            "b": p.get("barrio") or "",
            "s": p.get("source") or "",
            "f": num("freshness_days"),
            "usd": bool(p.get("is_usd_stable")),
            "lat": lat,
            "lng": lon,
            "img": primary_image,
        }

        depto = (p.get("state_province") or "").strip() or "unknown"
        by_depto.setdefault(depto, []).append(slim)

    # Build per-depto files
    manifest = {"generated_at": "", "deptos": []}
    total_size = 0

    for depto, records in sorted(by_depto.items(), key=lambda x: -len(x[1])):
        out_path = OUT_DIR / f"{slug(depto)}.json"
        body = {
            "depto": depto,
            "slug": slug(depto),
            "feature_count": len(records),
            "features": records,
        }
        json_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        size_kb = len(json_str.encode("utf-8")) / 1024
        total_size += size_kb
        manifest["deptos"].append({
            "depto": depto,
            "slug": slug(depto),
            "feature_count": len(records),
            "size_kb": round(size_kb, 1),
            "url": f"/data/search/{slug(depto)}.json",
        })
        if not args.dry_run:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json_str, encoding="utf-8")

    manifest["generated_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    manifest["total_features"] = sum(r["feature_count"] for r in manifest["deptos"])
    manifest["total_size_kb"] = round(total_size, 1)

    # Write manifest
    manifest_path = OUT_DIR / "_index.json"
    if not args.dry_run:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print summary
    print(f"  deptos: {len(by_depto)}")
    print(f"  total features: {manifest['total_features']:,}")
    print(f"  total size: {total_size:.1f} KB")
    print(f"  largest:")
    for d in manifest["deptos"][:5]:
        print(f"    {d['depto']:24s}  {d['feature_count']:>5}  {d['size_kb']:>5.1f} KB")

    if args.dry_run:
        print(f"  --dry-run: no writes")
        return 0

    print(f"  wrote {len(by_depto)} files to {OUT_DIR.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())