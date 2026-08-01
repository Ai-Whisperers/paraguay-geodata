#!/usr/bin/env python3
"""tools/build_mortgage_reference.py

Compute a static mortgage reference table for the most common loan sizes in
Paraguay, using the canonical artifact's median USD price and BCP-style
assumptions.  The viewer-side mortgage calculator already does live math;
this script produces a cached `mortgage_reference.json` for the FAQ and
landing-page summary tiles.

Output: exports/web/data/mortgage_reference.json
Schema:
{
  "generated_at": "...",
  "median_us_listing_price": 90000,
  "scenarios": [
    {"loan_usd": 50000, "years": 15, "rate_pct": 11.5, "monthly_usd": 587.50,
     "total_paid_usd": 105750, "interest_usd": 55750},
    ...
  ]
}

Assumptions:
  - 11.5% annual rate (typical BCP "tasa activa" for PY mortgage, 2026).
  - 70% LTV at the median listing price.
  - 15- and 25-year terms.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_RATE_PCT = 11.5
LOAN_TO_VALUE = 0.70


def _monthly_payment(principal: float, rate_pct: float, years: int) -> float:
    r = (rate_pct / 100) / 12
    n = years * 12
    if r == 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** -n)


def build(median_price_usd: float, rate_pct: float, ltv: float) -> dict:
    scenarios = []
    for years in (10, 15, 20, 25, 30):
        principal = median_price_usd * ltv
        monthly = _monthly_payment(principal, rate_pct, years)
        total_paid = monthly * years * 12
        interest = total_paid - principal
        scenarios.append({
            "loan_usd": round(principal),
            "years": years,
            "rate_pct": rate_pct,
            "monthly_usd": round(monthly, 2),
            "total_paid_usd": round(total_paid),
            "interest_usd": round(interest),
            "interest_to_principal_pct": round(interest / principal * 100, 1),
        })
    return {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "median_us_listing_price": round(median_price_usd),
        "ltv": ltv,
        "scenarios": scenarios,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path,
                    default=ROOT / "data/properties/canonical_properties.geojson")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "exports/web/data/mortgage_reference.json")
    ap.add_argument("--rate-pct", type=float, default=DEFAULT_RATE_PCT)
    ap.add_argument("--ltv", type=float, default=LOAN_TO_VALUE)
    args = ap.parse_args(argv)

    if not args.input.exists():
        sys.exit(f"input not found: {args.input}")
    feats = json.loads(args.input.read_text()).get("features") or []
    prices = [
        (f.get("properties") or {}).get("price_usd")
        for f in feats
        if (f.get("properties") or {}).get("price_usd") and
           (f.get("properties") or {}).get("listing_type") == "sale"
    ]
    prices = [p for p in prices if isinstance(p, (int, float)) and p > 0]
    if not prices:
        sys.exit("no usable prices in the canonical artifact")
    median = statistics.median(prices)
    payload = build(median, args.rate_pct, args.ltv)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK mortgage_reference: median ${payload['median_us_listing_price']:,}, "
          f"{len(payload['scenarios'])} scenarios at {args.rate_pct}% / {args.ltv} LTV")


if __name__ == "__main__":
    main()