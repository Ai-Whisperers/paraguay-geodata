#!/usr/bin/env python3
"""scripts/assemble_overpass_depts.py — assemble relation ways into Polygon features.

Inputs: /tmp/depts_geom2.json (relations + ways + nodes)
Output: exports/web/data/admin/departamentos.geojson
"""
import json
import sys
from collections import defaultdict
from pathlib import Path


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/depts_geom2.json")
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/root/paraguay-geodata/exports/web/data/admin/departamentos.geojson")

    raw = json.loads(src.read_text())
    elems = raw.get("elements", [])

    # Index nodes (id -> {lat, lon})
    nodes = {n["id"]: (n["lat"], n["lon"]) for n in elems if n["type"] == "node"}
    # Index ways (id -> [node_ids])
    ways = {w["id"]: w.get("nodes", []) for w in elems if w["type"] == "way"}

    # Index relations (id -> {tags, members[]})
    relations = {r["id"]: r for r in elems if r["type"] == "relation"}

    features = []
    for rel in relations.values():
        tags = rel.get("tags", {})
        iso = tags.get("ISO3166-2", "")
        if not iso.startswith("PY-"):
            continue
        # Collect outer + inner rings
        outer_ways = []
        inner_ways = []
        for m in rel.get("members", []):
            if m["type"] != "way":
                continue
            wid = m["ref"]
            role = m.get("role", "")
            if role == "inner":
                inner_ways.append(wid)
            else:
                outer_ways.append(wid)

        def way_to_coords(wid: int) -> list:
            if wid not in ways:
                return []
            coords = []
            for nid in ways[wid]:
                if nid in nodes:
                    lat, lon = nodes[nid]
                    coords.append([lon, lat])
            return coords

        # Build polygon
        outer_rings = []
        for wid in outer_ways:
            ring = way_to_coords(wid)
            if len(ring) >= 3:
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                outer_rings.append(ring)
        inner_rings = []
        for wid in inner_ways:
            ring = way_to_coords(wid)
            if len(ring) >= 3:
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                inner_rings.append(ring)

        if not outer_rings:
            continue

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon" if not inner_rings else "MultiPolygon",
                "coordinates": [outer_rings] if not inner_rings else [[outer_rings[0]] + inner_rings],
            },
            "properties": {
                "iso_code": iso,
                "name": tags.get("name", tags.get("name:en", "")),
                "name_es": tags.get("name:es", tags.get("name", "")),
                "admin_level": rel["type"],
                "osm_id": rel["id"],
                "wikidata": tags.get("wikidata", ""),
                "layer": "departamentos",
                "source": "OpenStreetMap (ODbL)",
                "source_date": "2026-07-11",
            },
        })

    dst.parent.mkdir(parents=True, exist_ok=True)
    fc = {"type": "FeatureCollection", "features": features}
    dst.write_text(json.dumps(fc, indent=2))
    print(f"wrote {dst} — {len(features)} dept features ({dst.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())