#!/usr/bin/env python3
"""tools/audit_properties.py

Quick health audit of the deployed properties artifact:
- all source_url fields are valid URLs
- geometry.coordinates look reasonable (PY bounding box)
- quality_flags / cluster_id / canonical_features / freshness_days populated
- per-source listing counts and median price

Usage: python3 -m tools.audit_properties [--input path] [--check-urls N]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import statistics
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

URL_RE = re.compile(r"^https?://[^\s]+$")
PY_BBOX = {"lon_min": -63.5, "lon_max": -54.0, "lat_min": -27.5, "lat_max": -19.0}


def _is_in_py(coords):
    if not isinstance(coords, list) or len(coords) < 2:
        return False
    lon, lat = coords[0], coords[1]
    return PY_BBOX["lon_min"] <= lon <= PY_BBOX["lon_max"] and PY_BBOX["lat_min"] <= lat <= PY_BBOX["lat_max"]


def audit(path: Path, check_urls: int = 0) -> int:
    raw = json.loads(path.read_text())
    feats = raw.get("features") or []
    if not feats:
        print("FAIL: no features")
        return 2

    by_source: dict[str, int] = collections.Counter()
    by_depto: dict[str, int] = collections.Counter()
    by_flag: dict[str, int] = collections.Counter()
    prices_by_source: dict[str, list[float]] = collections.defaultdict(list)
    issues: dict[str, int] = collections.Counter()
    placeholder_geom = 0
    bad_url = 0
    flagged = 0
    canonical_feature_seen = 0
    cluster_id_seen = 0
    freshness_seen = 0

    for f in feats:
        p = f.get("properties") or {}
        geo = f.get("geometry") or {}
        coords = geo.get("coordinates") or []

        # Source URL
        url = p.get("source_url") or ""
        if not URL_RE.match(url):
            bad_url += 1
        else:
            by_source[p.get("source") or "?"] += 1

        # Geometry
        if coords == [-57.6, -25.3]:
            placeholder_geom += 1
        if not _is_in_py(coords):
            issues["out_of_bounds"] += 1

        # Deptos
        d = p.get("state_province")
        if d:
            by_depto[d] += 1

        # Prices
        pr = p.get("price_usd")
        if isinstance(pr, (int, float)) and pr > 0:
            prices_by_source[p.get("source") or "?"].append(pr)

        # Quality flags
        for flag in p.get("quality_flags") or []:
            by_flag[flag] += 1
            flagged += 1

        if p.get("canonical_features"):
            canonical_feature_seen += 1
        if p.get("cluster_id"):
            cluster_id_seen += 1
        if p.get("freshness_days") is not None:
            freshness_seen += 1

    n = len(feats)
    print(f"features           : {n:,}")
    print(f"by_source          : {dict(by_source)}")
    print(f"by_depto (top 8)   : {dict(sorted(by_depto.items(), key=lambda x: -x[1])[:8])}")
    print(f"quality_flag counts: {dict(by_flag)}")
    print(f"flagged rows       : {flagged:,} ({flagged / n * 100:.1f}%)")
    print(f"placeholder geometry: {placeholder_geom:,}  (the Clasipar placeholder is [-57.6,-25.3])")
    print(f"out_of_bounds      : {issues['out_of_bounds']:,}")
    print(f"bad_source_url     : {bad_url:,}")
    print(f"has cluster_id     : {cluster_id_seen:,} ({cluster_id_seen / n * 100:.1f}%)")
    print(f"has canonical_features: {canonical_feature_seen:,} ({canonical_feature_seen / n * 100:.1f}%)")
    print(f"has freshness_days : {freshness_seen:,} ({freshness_seen / n * 100:.1f}%)")
    print()
    for src, prices in sorted(prices_by_source.items()):
        if prices:
            print(f"  {src:>15s}: median ${statistics.median(prices):>10,.0f}  (n={len(prices):,})")

    # Optional: HEAD-check the first N source URLs to make sure they actually
    # resolve (the user explicitly asked about live links).
    if check_urls > 0:
        import urllib.request
        urls = [f["properties"].get("source_url") for f in feats[:check_urls]]
        ok = 0
        fail: list[tuple[str, int]] = []
        for u in urls:
            try:
                req = urllib.request.Request(u, method="HEAD", headers={
                    "User-Agent": "paraguay-geodata/0.1"
                })
                with urllib.request.urlopen(req, timeout=10) as r:
                    if r.status < 400:
                        ok += 1
                    else:
                        fail.append((u, r.status))
            except Exception as e:
                fail.append((u, -1))
        print(f"\nurl check (HEAD {check_urls}): {ok}/{check_urls} OK")
        if fail:
            print("failures (url, status):")
            for u, st in fail[:5]:
                print(f"  {st:>3}  {u[:100]}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path,
                    default=ROOT / "exports/web/data/properties_latest.geojson")
    ap.add_argument("--check-urls", type=int, default=0,
                    help="HEAD-check the first N source URLs (0 to skip)")
    args = ap.parse_args(argv)
    if not args.input.exists():
        sys.exit(f"input not found: {args.input}")
    return audit(args.input, args.check_urls)


if __name__ == "__main__":
    sys.exit(main())