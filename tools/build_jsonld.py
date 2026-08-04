"""tools/build_jsonld.py — generate JSON-LD Dataset schema for SEO.

Reads data/properties/canonical_properties.geojson + data_freshness.json and
writes exports/web/index.html with a Schema.org Dataset block that describes:
  - the dataset name, description, license
  - the spatial coverage (Paraguay, with bounding box)
  - the temporal coverage (first/last scrape date)
  - the keywords (Asunción, listings, real estate, Paraguay)
  - the variables (price, area, bedrooms, currency, etc.)
  - the providers (4 portals)

This goes alongside the existing WebSite schema. Both blocks live in the
<head> so Google can read them at crawl time.

Usage:
  python3 -m tools.build_jsonld
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANON = REPO / "data" / "properties" / "canonical_properties.geojson"
FRESH = REPO / "exports" / "web" / "data" / "data_freshness.json"
INDEX = REPO / "exports" / "web" / "index.html"


def build_dataset_block() -> dict:
    """Build the Dataset JSON-LD object from live data."""
    canon = json.loads(CANON.read_text())
    fresh = json.loads(FRESH.read_text())

    features = canon.get("features", [])
    n = len(features)

    # Compute temporal coverage (ISO 8601 interval: 2026-07-11/2026-08-04)
    dates = sorted(
        f["properties"].get("last_seen_at", "")
        for f in features if f["properties"].get("last_seen_at")
    )
    first_date = dates[0][:10] if dates else ""  # YYYY-MM-DD
    last_date = dates[-1][:10] if dates else ""

    # Spatial coverage — Paraguay bounding box (rough)
    bbox = [-62.5, -27.5, -54.0, -19.3]

    # Variables (the structured fields exposed)
    variables = [
        {
            "@type": "PropertyValue",
            "name": "price_usd",
            "description": "Listing price in USD (or converted from PYG)",
        },
        {
            "@type": "PropertyValue",
            "name": "area_ha",
            "description": "Property area in hectares (sqm / 10000)",
        },
        {
            "@type": "PropertyValue",
            "name": "bedrooms",
            "description": "Number of bedrooms (0 for studios or vacant land)",
        },
        {
            "@type": "PropertyValue",
            "name": "property_type",
            "description": "One of apartment, house, land, commercial, office",
        },
        {
            "@type": "PropertyValue",
            "name": "state_province",
            "description": "One of Paraguay's 17 departments + Asunción",
        },
        {
            "@type": "PropertyValue",
            "name": "currency",
            "description": "Either USD or PYG",
        },
        {
            "@type": "PropertyValue",
            "name": "source",
            "description": "Originating portal (infocasas, tulugar, etc)",
        },
    ]

    # Providers (sources we crawl)
    sources = set()
    for f in features:
        s = f["properties"].get("source")
        if s:
            sources.add(s)

    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Paraguay Real Estate Listings — Open Aggregator",
        "alternateName": "Paraguay Geodata Listings",
        "description": (
            f"{n:,} active real estate listings across Paraguay, "
            "aggregated from multiple public portals. "
            "Updated weekly with cross-source deduplication."
        ),
        "url": "https://geodata.paragu-ai.com/",
        "identifier": "py-geo-listings",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "spatialCoverage": {
            "@type": "Place",
            "name": "Paraguay",
            "geo": {
                "@type": "GeoShape",
                "box": " ".join(str(c) for c in bbox),  # "minLon minLat maxLon maxLat"
            },
        },
        "temporalCoverage": f"{first_date}/{last_date}",
        "keywords": [
            "Paraguay", "real estate", "listings", "Asunción",
            "Alto Paraná", "Central", "Cordillera",
            "departamentos", "casas", "terrenos", "lotes",
        ],
        "variableMeasured": variables,
        "provider": {
            "@type": "Organization",
            "name": "Ai-Whisperers",
            "url": "https://github.com/Ai-Whisperers/paraguay-geodata",
        },
        "sourceOrganization": [
            {"@type": "Organization", "name": s, "url": ""}
            for s in sorted(sources)
        ],
        "distribution": {
            "@type": "DataDownload",
            "encodingFormat": "application/geo+json",
            "contentUrl": "https://geodata.paragu-ai.com/data/properties_latest.geojson",
            "contentSize": str(CANON.stat().st_size),
        },
        "dateModified": fresh.get("as_of_utc") or datetime.datetime.utcnow().isoformat() + "Z",
    }


def inject_into_html(block: dict) -> None:
    """Inject the Dataset JSON-LD block into index.html."""
    html = INDEX.read_text()

    block_str = json.dumps(block, ensure_ascii=False, indent=4)
    script = f'<script type="application/ld+json">\n{block_str}\n    </script>'

    # Find the existing JSON-LD block and insert a new one after it
    m = re.search(r'(<script type="application/ld\+json">.*?</script>)', html, re.DOTALL)
    if m:
        pos = m.end()
        # Insert the Dataset block after the existing WebSite block
        html = html[:pos] + "\n    " + script + html[pos:]
        INDEX.write_text(html)
        print(f"  ✓ injected Dataset JSON-LD after WebSite schema")
    else:
        # No existing JSON-LD, append to <head>
        html = html.replace("</head>", script + "\n</head>")
        INDEX.write_text(html)
        print(f"  ✓ appended Dataset JSON-LD to <head>")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build JSON-LD Dataset schema from live data.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not CANON.exists():
        print(f"  ERR: {CANON} not found")
        return 1
    if not INDEX.exists():
        print(f"  ERR: {INDEX} not found")
        return 1

    print("=== build_jsonld ===")
    block = build_dataset_block()
    print(f"  variables: {len(block['variableMeasured'])}")
    print(f"  sources: {len(block['sourceOrganization'])}")
    print(f"  coverage: {block['temporalCoverage']}")

    if args.dry_run:
        print(f"  --dry-run: no writes")
        print(f"\n{json.dumps(block, ensure_ascii=False, indent=2)[:800]}...")
        return 0

    inject_into_html(block)
    return 0


if __name__ == "__main__":
    sys.exit(main())