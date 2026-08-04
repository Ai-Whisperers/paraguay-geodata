"""tools/infer_property_type.py — infer missing property_type from title + area + bedrooms.

The canonical pipeline classifies most listings via the _PROPERTY_TYPE_NORMALIZE
taxonomy. But 1,183 listings (11.0%) end up with property_type=None or
"unknown" — usually because the source data didn't expose it as a structured
field.

This tool runs *after* canonicalize and patches the inferred values, in
priority order:

  1. Title tokens (most reliable — 80% of cases)
  2. Area thresholds (1,000+ sqm → land; 50-200 sqm → apartment)
  3. Bedrooms (0 → land; 1-2 → apartment; 3+ → house)
  4. Combined heuristics (e.g. "Casa con terreno de 1,000m²" → house wins)

Usage:
  python3 -m tools.infer_property_type
  python3 -m tools.infer_property_type --dry-run
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANON_PATH = REPO / "data" / "properties" / "canonical_properties.geojson"


# Title token → canonical type. Longest patterns first so "departamento" is
# matched before "depto".
TITLE_PATTERNS = [
    (re.compile(r"\b(departamento|depto\.?s?|apartamento|apto\.?s?|flat|loft|penthouse|edificio)\b", re.IGNORECASE), "apartment"),
    (re.compile(r"\b(casa|casona|quinta|vivienda|chalet|home)\b", re.IGNORECASE), "house"),
    (re.compile(r"\b(terreno|lote|campo|finca|granja|hacienda|terrenos)\b", re.IGNORECASE), "land"),
    (re.compile(r"\b(galp[oó]n|dep[oó]sito|bodega|cochera|garaje|local|shop|tienda|store)\b", re.IGNORECASE), "commercial"),
    (re.compile(r"\b(oficina|oficinas|consultorio)\b", re.IGNORECASE), "office"),
]


def infer_from_title(title: str) -> str | None:
    """Return canonical property type from title, or None if no match."""
    if not title:
        return None
    # Score each candidate by pattern position (earlier wins on ties).
    candidates = []
    for pat, ptype in TITLE_PATTERNS:
        m = pat.search(title)
        if m:
            candidates.append((m.start(), ptype))
    if not candidates:
        return None
    # Pick the earliest match (most prominent in title). On ties, prefer
    # house > apartment > land > commercial > office so "Casa con terreno"
    # → house rather than land.
    priority = {"house": 5, "apartment": 4, "land": 3, "commercial": 2, "office": 1}
    candidates.sort(key=lambda c: (c[0], -priority.get(c[1], 0)))
    return candidates[0][1]


def infer_from_area(area_ha: float | None) -> str | None:
    """Return canonical type from area. Listings >1,000 ha are usually land;
    50-200 sqm is usually apartment; >200 sqm is usually house."""
    if not area_ha or area_ha <= 0:
        return None
    if area_ha >= 50:
        return "land"
    sqm = area_ha * 10000
    if sqm >= 200:
        return "house"
    if sqm >= 30:
        return "apartment"
    return "land"


def infer_from_bedrooms(bedrooms: int | None) -> str | None:
    """Return canonical type from bedrooms."""
    if bedrooms is None:
        return None
    if bedrooms == 0:
        return "land"
    if bedrooms <= 2:
        return "apartment"
    return "house"


def infer_property_type(props: dict) -> tuple[str, str] | None:
    """Return (canonical_type, source) from inference rules, or None if no signal."""
    ptype = props.get("property_type")
    title = props.get("title") or ""
    area_ha = props.get("area_ha")
    bedrooms = props.get("bedrooms")

    # Title first — most reliable
    t = infer_from_title(title)
    if t:
        return t, "title"

    # Area next
    a = infer_from_area(area_ha)
    if a:
        return a, "area"

    # Bedrooms last
    b = infer_from_bedrooms(bedrooms)
    if b:
        return b, "bedrooms"

    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Infer missing property_type from title/area/bedrooms.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not CANON_PATH.exists():
        print(f"  ERR: {CANON_PATH} not found — run canonicalize_properties first")
        return 1

    print("=== infer_property_type ===")

    data = json.loads(CANON_PATH.read_text())
    features = data.get("features", [])
    n = len(features)
    print(f"  loaded {n:,} features")

    n_unknown_before = sum(1 for f in features
                          if f["properties"].get("property_type") in (None, "", "unknown"))
    print(f"  unknown/null property_type: {n_unknown_before:,}")

    n_inferred = 0
    by_source = collections.Counter()
    by_type = collections.Counter()

    for f in features:
        p = f["properties"]
        if p.get("property_type") not in (None, "", "unknown"):
            continue
        result = infer_property_type(p)
        if result is None:
            continue
        ptype, source = result
        p["property_type"] = ptype
        p["property_type_source"] = f"inferred_{source}"
        n_inferred += 1
        by_source[source] += 1
        by_type[ptype] += 1

    n_unknown_after = n_unknown_before - n_inferred
    print(f"  inferred: {n_inferred:,} (was unknown {n_unknown_before:,}, now {n_unknown_after:,})")
    print(f"  by source: {dict(by_source)}")
    print(f"  by type: {dict(by_type)}")

    if args.dry_run:
        print(f"  --dry-run: no writes")
        return 0

    data["features"] = features
    data["generated_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    CANON_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  wrote {CANON_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
