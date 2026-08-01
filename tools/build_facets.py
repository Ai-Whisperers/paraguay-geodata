"""tools/build_facets.py

Generate `data/properties/facets.json` — the small artifact the viewer loads at
boot to populate filter dropdowns (depto, property_type, currency, source) and
display counts in the Insights panel.

Schema
------
{
  "generated_at": ISO-8601,
  "feature_count": int,
  "facets": {
    "depto":         [{"value": "Central", "count": 4425}, ...],
    "property_type": [{"value": "land", "count": 4218}, ...],
    "currency":      [{"value": "USD", "count": 5191}, ...],
    "source":        [{"value": "tulugar", "count": 10310}, ...],
    "features":      [{"value": "pool", "count": 2682}, ...]
  },
  "freshness": {"min": "...", "max": "...", "median_days": 20},
  "quality": {
    "total": 10754,
    "clean": 5681,
    "flagged": 5073,
    "by_flag": {"currency_conflict": 4747, ...}
  }
}
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(canonical_path: Path) -> dict:
    raw = json.loads(canonical_path.read_text())
    feats = raw.get("features") or []

    counter: dict[str, collections.Counter] = {
        "depto": collections.Counter(),
        "property_type": collections.Counter(),
        "currency": collections.Counter(),
        "source": collections.Counter(),
        "features": collections.Counter(),
    }
    quality = collections.Counter()
    freshness_days: list[int] = []
    scraped_at: list[str] = []

    for f in feats:
        p = f.get("properties") or {}
        counter["depto"][p.get("state_province") or "?"] += 1
        counter["property_type"][p.get("property_type") or "?"] += 1
        counter["currency"][p.get("currency") or "?"] += 1
        counter["source"][p.get("source") or "?"] += 1
        for x in (p.get("canonical_features") or []):
            counter["features"][x] += 1
        flags = p.get("quality_flags") or []
        if flags:
            quality.update(flags)
        if p.get("freshness_days") is not None:
            freshness_days.append(int(p["freshness_days"]))
        if p.get("last_seen_at"):
            scraped_at.append(p["last_seen_at"])

    out = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "feature_count": len(feats),
        "facets": {
            k: [{"value": v, "count": c} for v, c in sorted(counter[k].items(), key=lambda kv: -kv[1])]
            for k in counter
        },
        "freshness": {
            "min":  min(scraped_at) if scraped_at else None,
            "max":  max(scraped_at) if scraped_at else None,
            "median_days": int(statistics.median(freshness_days)) if freshness_days else None,
        },
        "quality": {
            "total":   len(feats),
            "clean":   len(feats) - sum(1 for f in feats if (f.get("properties") or {}).get("quality_flags")),
            "flagged": sum(1 for f in feats if (f.get("properties") or {}).get("quality_flags")),
            "by_flag": dict(sorted(quality.items(), key=lambda kv: -kv[1])),
        },
    }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path,
                    default=ROOT / "data/properties/canonical_properties.geojson")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "data/properties/facets.json")
    args = ap.parse_args(argv)
    if not args.input.exists():
        sys.exit(f"input not found: {args.input}  (run canonicalize_properties first)")
    payload = build(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK facets: {payload['feature_count']:,} features, "
          f"{payload['quality']['flagged']:,} flagged, "
          f"{len(payload['facets'])} facet groups")


if __name__ == "__main__":
    main()