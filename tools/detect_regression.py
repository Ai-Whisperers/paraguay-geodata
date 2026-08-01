#!/usr/bin/env python3
"""tools/detect_regression.py

Hard guardrail against bad scrapes silently shrinking the public artifact.
Compares the freshly canonicalized GeoJSON against the currently deployed one
and fails the deploy if key counts drop more than `max_shrink_pct`.

Usage
-----
    python3 -m tools.detect_regression \\
        --current data/properties/canonical_properties.geojson \\
        --last    exports/web/data/properties_latest.geojson \\
        --max-shrink-pct 30
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _summarize(g: dict) -> dict:
    feats = g.get("features") or []
    depto = collections.Counter()
    pt = collections.Counter()
    cur = collections.Counter()
    for f in feats:
        p = (f.get("properties") or {})
        depto[p.get("state_province") or "?"] += 1
        pt[p.get("property_type") or "?"] += 1
        cur[p.get("currency") or "?"] += 1
    return {
        "feature_count": len(feats),
        "deptos": dict(depto.most_common()),
        "property_types": dict(pt.most_common()),
        "currencies": dict(cur.most_common()),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--current", type=Path, required=True)
    ap.add_argument("--last", type=Path, required=True)
    ap.add_argument("--max-shrink-pct", type=float, default=30.0)
    args = ap.parse_args(argv)

    cur = _summarize(_load(args.current))
    last = _summarize(_load(args.last))

    delta = (cur["feature_count"] - last["feature_count"]) / max(last["feature_count"], 1) * 100
    if -delta > args.max_shrink_pct:
        print(f"FAIL shrink {delta:.1f}% exceeds -{args.max_shrink_pct}%",
              file=sys.stderr)
        print(f"  last={last['feature_count']:,}, current={cur['feature_count']:,}",
              file=sys.stderr)
        return 1

    # Require 17+ deptos only if we have a meaningful number of rows.  Tiny
    # synthetic slices (< 2000 features) are likely fixture noise, not data
    # regression.
    if cur["feature_count"] >= 2000 and len(cur["deptos"]) < 17:
        print(f"FAIL only {len(cur['deptos'])} deptos found (expected >= 17)",
              file=sys.stderr)
        return 2

    print(f"OK diff = {delta:+.2f}% "
          f"(last={last['feature_count']:,}, current={cur['feature_count']:,}, "
          f"deptos={len(cur['deptos'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())