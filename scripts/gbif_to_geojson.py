#!/usr/bin/env python3
"""scripts/gbif_to_geojson.py — convert GBIF response to GeoJSON FeatureCollection.

Run: python3 scripts/gbif_to_geojson.py <input.json> <output.geojson> [limit]
"""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])

raw = json.loads(src.read_text())
features = []
for r in raw.get("results", []):
    lat = r.get("decimalLatitude")
    lon = r.get("decimalLongitude")
    if lat is None or lon is None:
        continue
    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "species": r.get("species", "unknown"),
            "kingdom": r.get("kingdom", "unknown"),
            "family": r.get("family", ""),
            "event_date": r.get("eventDate", ""),
            "layer": "gbif_paraguay",
            "source": "GBIF",
            "license": r.get("license", ""),
        },
    })
dst.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2))
print(f"wrote {dst}: {len(features)} features, {dst.stat().st_size:,} bytes")
unique_species = len(set(f["properties"]["species"] for f in features))
kingdoms = {}
for f in features:
    k = f["properties"]["kingdom"]
    kingdoms[k] = kingdoms.get(k, 0) + 1
print(f"unique species: {unique_species}")
print(f"by kingdom: {kingdoms}")