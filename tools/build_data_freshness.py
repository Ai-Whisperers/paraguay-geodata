#!/usr/bin/env python3
"""tools/build_data_freshness.py

Emit `exports/web/data/data_freshness.json` from the canonical artifact.
The viewer reads this to render the freshness badge.

Schema (consumed by fetchDataFreshness() in index.html)
--------------------------------------------------------
{
  "as_of_utc":  "2026-07-31T08:00:00Z",
  "min_seen":   "2026-07-11T04:32:08+00:00",
  "max_seen":   "2026-07-11T05:44:33+00:00",
  "median_days": 21,
  "feature_count": 10754,
  "sources": {
    "infocasas":  {"reachable": true,  "count": 444},
    "tulugar":    {"reachable": true,  "count": 10310},
    "catastro":   {"reachable": true,  "count": 0},
    ...
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
    freshness_days: list[int] = []
    source_counts: dict[str, int] = collections.Counter()
    for f in feats:
        p = f.get("properties") or {}
        if p.get("freshness_days") is not None:
            freshness_days.append(int(p["freshness_days"]))
        if p.get("source"):
            source_counts[p["source"]] += 1
    sources = {
        s: {"reachable": True, "count": c}
        for s, c in sorted(source_counts.items())
    }
    return {
        "as_of_utc": raw.get("generated_at") or __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "feature_count": len(feats),
        "median_days": int(statistics.median(freshness_days)) if freshness_days else None,
        "sources": sources,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path,
                    default=ROOT / "data/properties/canonical_properties.geojson")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "exports/web/data/data_freshness.json")
    args = ap.parse_args(argv)
    if not args.input.exists():
        sys.exit(f"input not found: {args.input}")
    payload = build(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK freshness: median {payload['median_days']}d, "
          f"{payload['feature_count']:,} features, "
          f"{len(payload['sources'])} sources")


if __name__ == "__main__":
    main()