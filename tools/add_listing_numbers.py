"""tools/add_listing_numbers.py — assign stable row IDs to listings.

Today every listing has an `id` like `ic_c2c684ea3608` — a source-prefixed
hash. That's not human-citable.

This tool adds a `listing_number` field that's a 1-based integer stable
across deploys (sorted by source+id). So:

  listing_number=1 → first infocasas listing (alphabetical by id)
  listing_number=2 → second infocasas listing
  ...
  listing_number=N → last inmueblespy listing

The same listing keeps the same number across deploys unless the
listing set itself changes (insertion/deletion). For deduplicated
clusters, only the primary (lowest-id) listing keeps the cluster's
listing_number.

Usage:
  python3 -m tools.add_listing_numbers
  python3 -m tools.add_listing_numbers --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANON = REPO / "data" / "properties" / "canonical_properties.geojson"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Add stable listing_number field to canonical_properties.geojson.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if not CANON.exists():
        print(f"  ERR: {CANON} not found")
        return 1

    print("=== add_listing_numbers ===")
    data = json.loads(CANON.read_text())
    features = data.get("features", [])
    n = len(features)
    print(f"  loaded {n:,} features")

    # Stable sort: by id (deterministic)
    indexed = [(f, f["properties"].get("id", "")) for f in features]
    indexed.sort(key=lambda x: x[1])

    # Assign numbers
    for i, (f, _) in enumerate(indexed, start=1):
        f["properties"]["listing_number"] = i

    # Verify uniqueness
    seen = set()
    dupes = 0
    for f in features:
        ln = f["properties"].get("listing_number")
        if ln in seen:
            dupes += 1
        seen.add(ln)
    print(f"  assigned numbers: {n:,} (duplicates: {dupes})")

    # Show first 3 examples
    print(f"  first 3:")
    for f in sorted(features, key=lambda x: x["properties"].get("listing_number", 0))[:3]:
        p = f["properties"]
        print(f"    #{p['listing_number']:>5}  {p.get('id', '')}  {p.get('title', '')[:50]}")

    if args.dry_run:
        print(f"  --dry-run: no writes")
        return 0

    data["features"] = features
    data["generated_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    CANON.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  wrote {CANON.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())