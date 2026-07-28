#!/usr/bin/env python3
"""Build the paid national AutoCAD DXF artifact from public GeoJSON.

The file intentionally uses the same AutoCAD R12 point-entity model as the
browser's free DXF exporter. See the project-level architect pricing runbook
and the static-site-geospatial-bugfix skill for the delivery contract.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def clean_text(value: Any, limit: int = 255) -> str:
    text = str(value or "")
    text = " ".join(text.replace("\x00", " ").split())
    return text[:limit]


def point_features(collection: dict[str, Any]) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for feature in collection.get("features", []):
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates")
        if geometry.get("type") != "Point" or not isinstance(coordinates, list) or len(coordinates) < 2:
            continue
        lon, lat = coordinates[:2]
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            continue
        if not math.isfinite(lon) or not math.isfinite(lat):
            continue
        features.append(feature)
    return features


def build_dxf(collection: dict[str, Any]) -> str:
    features = point_features(collection)
    if not features:
        raise ValueError("input has no valid Point features")

    centroid_lon = sum(feature["geometry"]["coordinates"][0] for feature in features) / len(features)
    centroid_lat = sum(feature["geometry"]["coordinates"][1] for feature in features) / len(features)
    metres_per_degree_lat = 111_320
    metres_per_degree_lon = metres_per_degree_lat * math.cos(math.radians(centroid_lat))

    lines: list[str] = []

    def push(*values: object) -> None:
        lines.extend(str(value) for value in values)

    push("  0", "SECTION", "  2", "HEADER")
    push("  9", "$ACADVER", "  1", "AC1009")
    push("  9", "$INSUNITS", " 70", "6")
    push("  0", "ENDSEC")
    push("  0", "SECTION", "  2", "TABLES")
    push("  0", "TABLE", "  2", "LAYER")
    push("  0", "LAYER", "  2", "PROPERTIES", " 70", "0", " 62", "7", "  6", "CONTINUOUS")
    push("  0", "ENDTAB", "  0", "ENDSEC")
    push("  0", "SECTION", "  2", "ENTITIES")

    for feature in features:
        lon, lat = feature["geometry"]["coordinates"][:2]
        properties = feature.get("properties") or {}
        x = (lon - centroid_lon) * metres_per_degree_lon
        y = (lat - centroid_lat) * metres_per_degree_lat
        title = clean_text(properties.get("title") or properties.get("source_id") or "Property")

        push("  0", "POINT", "  8", "PROPERTIES")
        push(" 10", f"{x:.3f}", " 20", f"{y:.3f}", " 30", "0.0")
        push("1001", "PARAGUAY_GEODATA", "1000", title)
        if properties.get("price_usd"):
            push("1000", f"USD {round(properties['price_usd']):,}")
        if properties.get("area_ha"):
            push("1000", f"{clean_text(properties['area_ha'])} ha")
        if properties.get("city"):
            push("1000", clean_text(properties["city"]))
        if properties.get("source_url"):
            push("1000", clean_text(properties["source_url"]))

    push("  0", "ENDSEC", "  0", "EOF")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("exports/web/data/properties_latest.geojson"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("exports/web/data/properties_latest.dxf"),
    )
    args = parser.parse_args()

    collection = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_dxf(collection)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8", newline="\n")
    print(f"wrote {args.output} ({len(point_features(collection)):,} points, {args.output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
