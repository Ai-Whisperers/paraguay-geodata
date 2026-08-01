#!/usr/bin/env python3
"""tools/build_days_on_market.py

Estimates days-on-market per depto from the canonical artifact by comparing
each listing's `first_seen_at` (today, since we don't yet have history) to a
back-fill of freshness_days.

For now the estimator is a simple "freshness_days" reading; a future version
will use `scripts/track_price_history.py` to keep a per-listing history table
and compute true DoM.

Outputs:
    data/properties/days_on_market.json
        {
          "generated_at": "...",
          "summary": { "median_days": 21, "p25": ..., "p75": ... },
          "by_depto": { "Central": {"median_days":..., "n":...}, ... },
          "stale_listings": [ ... top 50 by freshness_days desc ... ]
        }

Usage:
    python3 -m tools.build_days_on_market
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _percentile(values: list, pct: int) -> int | None:
    """Standard linear-interpolation percentile (numpy default)."""
    if not values:
        return None
    if len(values) == 1:
        return int(values[0])
    s = sorted(values)
    k = (len(s) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return int(s[f])
    return int(s[f] + (s[c] - s[f]) * (k - f))


def build(features: list[dict]) -> dict:
    by_depto: dict[str, list[int]] = collections.defaultdict(list)
    all_days: list[int] = []
    stale: list[dict] = []
    for f in features:
        p = f.get("properties") or {}
        d = p.get("freshness_days")
        if d is None:
            continue
        all_days.append(int(d))
        depto = p.get("state_province") or "Unknown"
        by_depto[depto].append(int(d))
        stale.append({
            "id": p.get("id"),
            "title": p.get("title"),
            "depto": depto,
            "freshness_days": int(d),
            "source": p.get("source"),
            "source_url": p.get("source_url"),
        })
    stale.sort(key=lambda r: -r["freshness_days"])
    return {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "summary": {
            "median_days": int(statistics.median(all_days)) if all_days else None,
            "p25": _percentile(all_days, 25),
            "p75": _percentile(all_days, 75),
            "n_listings": len(all_days),
        },
        "by_depto": {
            d: {
                "median_days": int(statistics.median(days)) if len(days) >= 3 else None,
                "n": len(days),
                "stale_pct": round(sum(1 for x in days if x > 30) / len(days) * 100, 1) if days else 0,
            } for d, days in sorted(by_depto.items())
        },
        "stale_listings": stale[:50],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path,
                    default=ROOT / "data/properties/canonical_properties.geojson")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "exports/web/data/days_on_market.json")
    args = ap.parse_args(argv)
    if not args.input.exists():
        sys.exit(f"input not found: {args.input}")
    feats = json.loads(args.input.read_text()).get("features") or []
    payload = build(feats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK days-on-market: median {payload['summary']['median_days']}d, "
          f"{payload['summary']['n_listings']:,} listings, "
          f"{len(payload['stale_listings'])} flagged stale")


if __name__ == "__main__":
    main()