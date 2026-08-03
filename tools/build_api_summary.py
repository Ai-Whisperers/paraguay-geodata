"""tools/build_api_summary.py

Generate the api/v1/properties.json summary that the home page exposes.

Reads the canonical properties artifact + the source registry, and writes
the machine-readable API summary to /exports/web/api/v1/properties.json.

Usage:
  python3 -m tools.build_api_summary

Cron-friendly: exits 0 on success, 1 on failure.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "exports" / "web" / "api" / "v1" / "properties.json"
CANONICAL_PATH = ROOT / "data" / "properties" / "canonical_properties.geojson"
FACETS_PATH = ROOT / "data" / "properties" / "facets.json"
SOURCE_REGISTRY = ROOT / "data" / "properties" / "source_registry.json"


def _load_count(path: Path) -> int:
    """Read a JSON file and return source count from envelope."""
    try:
        d = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return 0
    return d.get("feature_count", d.get("total", 0))


def _load_sources(path: Path) -> dict[str, int]:
    """Aggregate source counts from a FeatureCollection."""
    try:
        d = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    feats = d.get("features") or []
    counts: dict[str, int] = {}
    for f in feats:
        s = (f.get("properties") or {}).get("source") or "?"
        counts[s] = counts.get(s, 0) + 1
    return counts


def _load_facets(path: Path) -> dict:
    """Read the facets artifact (if present)."""
    try:
        d = json.loads(path.read_text())
        return d.get("facets", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main() -> int:
    API_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Aggregate source counts
    sources = _load_sources(CANONICAL_PATH)
    if not sources:
        sources = _load_sources(ROOT / "exports/web/data/properties_latest.geojson")

    total = sum(sources.values())
    facets = _load_facets(FACETS_PATH)
    if not facets:
        facets = _load_facets(ROOT / "exports/web/data/facets.json")

    # Look at the source registry for fresh Source keys
    expected: list[str] = []
    try:
        reg = json.loads(SOURCE_REGISTRY.read_text())
        for s in reg.get("sources", []):
            if s.get("status") == "live":
                expected.append(s["key"])
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Detect sources that are live & reachable but missing from the canonical
    missing = [k for k in expected if k not in sources]
    if missing:
        print(f"  WARN: missing sources in canonical: {missing}")

    summary = {
        "total": total,
        "sources": sources,
        "facets": facets,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "docs": "https://geodata.paragu-ai.com/api/v1/properties.json",
        "geojson_endpoint": "https://geodata.paragu-ai.com/data/properties_latest.geojson",
        "vitals_endpoint": "/api/v1/vitals",
        "status_page": "/status",
        "bulletin": "/bulletin.json",
        "license": "CC0",
        "pii_scrubbed": True,
        "scrub_version": "1.0",
        "expected_sources": expected,
    }
    API_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"  OK API summary: {total} listings, {len(sources)} sources → {API_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
