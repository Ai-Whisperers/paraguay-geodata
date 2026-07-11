#!/usr/bin/env python3
"""scripts/merge_snapshots.py — merge all per-dept property snapshots into one deduped GeoJSON."""
import json, glob, sys
from pathlib import Path

snap_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "/root/paraguay-geodata/data/properties/snapshots")
out_path = Path(sys.argv[2] if len(sys.argv) > 2 else "/root/paraguay-geodata/exports/web/data/properties_latest.geojson")

files = sorted(snap_dir.glob("*_2026-07-11_*.geojson"))
by_slug = {}
for f in files:
    slug = f.name.split("_2026")[0]
    if by_slug.get(slug) is None or f.stat().st_mtime > by_slug[slug].stat().st_mtime:
        by_slug[slug] = f

print(f"Per-dept snapshots: {len(by_slug)} deptos")
seen = {}
features = []
for slug, f in sorted(by_slug.items()):
    d = json.loads(f.read_text())
    n_added = 0
    for rec in d.get("raw_records", []):
        if rec.get("lat") is None:
            continue
        rid = rec.get("id")
        if rid in seen:
            continue
        seen[rid] = True
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [rec["lon"], rec["lat"]]},
            "properties": {k: v for k, v in rec.items() if k not in ("lat", "lon")},
        })
        n_added += 1
    print(f"  {slug:25s}: +{n_added}")
out = {"type": "FeatureCollection", "features": features}
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(f"TOTAL: {len(features)} listings ({out_path.stat().st_size:,} bytes)")