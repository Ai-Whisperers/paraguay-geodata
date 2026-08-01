#!/usr/bin/env python3
"""tools/image_dedup.py

Cross-source image deduplication using perceptual hashing (pHash 8x8 = 64 bits).
Two images with a Hamming distance ≤ 5 on their phash are considered the
same photo and therefore the same listing.  We use this to detect when the
same finca appears on multiple portals under different titles.

Pipeline
--------
1.  Read the canonical properties GeoJSON.
2.  For every feature, fetch the FIRST image URL (HEAD or GET; ignore
    failures — listings without photos still go into the "no-image" bucket).
3.  Compute the 64-bit phash of each decoded image.
4.  Group by Hamming distance <= 5; emit clusters.

CLI
---
    python3 -m tools.image_dedup \\
        --input data/properties/canonical_properties.geojson \\
        --output data/properties/image_clusters.json \\
        --max-rows 500      # safety cap (network-bound)

    # with a mock (no network) for CI:
    python3 -m tools.image_dedup --mock

Outputs
-------
{
  "generated_at": "...",
  "input_rows":   10754,
  "fetched":      500,
  "clustered":    312,
  "clusters": [
    {
      "cluster_id": "img-…",
      "size": 3,
      "properties": ["tulugar-…", "infocasas-…", "clasipar-…"]
    },
    ...
  ],
  "no_image":   [...source_ids without a usable image URL]
}
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import sys
import time
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

HAMMING_THRESHOLD = 5
MAX_FETCH = 80  # per row: trust the first non-empty image URL
FETCH_TIMEOUT = 8  # seconds
USER_AGENT = "paraguay-geodata/0.1 (+github.com/Ai-Whisperers/paraguay-geodata)"


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _hash_features(features: list[dict], limit: int | None) -> tuple[list[dict], list[str]]:
    """Return (hashed_rows, no_image_source_ids).  Each hashed row has
    {source, source_id, source_url, image_url, phash:int}.
    """
    out: list[dict] = []
    no_image: list[str] = []
    for f in features:
        p = f.get("properties") or {}
        if p.get("listing_type") and p["listing_type"] != "sale":
            continue
        imgs = p.get("images") or []
        url = next((u for u in imgs if u), None)
        if not url:
            no_image.append(p.get("source_id") or p.get("id") or "?")
            continue
        out.append({
            "source": p.get("source") or "?",
            "source_id": p.get("source_id") or p.get("id") or "?",
            "source_url": p.get("source_url"),
            "image_url": url,
            "title": p.get("title"),
            "cluster_id": p.get("cluster_id"),
        })
        if limit and len(out) >= limit:
            break
    return out, no_image


def _fetch_phash(rows: list[dict], sleep_s: float = 0.05) -> tuple[list[dict], list[dict]]:
    """Returns (ok, fail).  ok rows have a `phash` int added."""
    import urllib.request
    import imagehash
    from PIL import Image  # noqa: F401  (Pillow)

    ok: list[dict] = []
    fail: list[dict] = []
    for i, row in enumerate(rows):
        try:
            req = urllib.request.Request(row["image_url"], headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
                data = resp.read(2_000_000)  # 2 MB cap
            img = Image.open(io.BytesIO(data)).convert("RGB")
            row["phash"] = int(str(imagehash.phash(img)), 16)  # 64-bit hex → int
            ok.append(row)
        except Exception as exc:
            row["error"] = str(exc)[:80]
            fail.append(row)
        if sleep_s and (i + 1) % 25 == 0:
            time.sleep(sleep_s * 5)  # batched throttle
    return ok, fail


def _cluster(ok: list[dict]) -> list[dict]:
    """Greedy O(N²) cluster by Hamming distance <= HAMMING_THRESHOLD."""
    parent = list(range(len(ok)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(len(ok)):
        for j in range(i + 1, len(ok)):
            if _hamming(ok[i]["phash"], ok[j]["phash"]) <= HAMMING_THRESHOLD:
                union(i, j)

    groups: dict[int, list[int]] = collections.defaultdict(list)
    for i in range(len(ok)):
        groups[find(i)].append(i)

    clusters: list[dict] = []
    for root, members in groups.items():
        if len(members) <= 1:
            continue
        cluster_id = "img-" + hashlib.sha1(
            ",".join(str(ok[m]["phash"]) for m in members).encode("utf-8")
        ).hexdigest()[:10]
        clusters.append({
            "cluster_id": cluster_id,
            "size": len(members),
            "properties": [
                {
                    "source": ok[m]["source"],
                    "source_id": ok[m]["source_id"],
                    "source_url": ok[m]["source_url"],
                    "title": ok[m]["title"],
                    "cluster_id": ok[m]["cluster_id"],
                } for m in members
            ],
        })
    return clusters


def _mock_run(features: list[dict], limit: int) -> dict:
    """Deterministic offline path used by the test suite."""
    rows, no_image = _hash_features(features, limit=limit)
    # Force identical phashes for the first 4 rows so the test suite can
    # assert that duplicate detection works without network.
    for i in range(min(4, len(rows))):
        rows[i]["phash"] = 0xDEADBEEFCAFEBABE
    for i in range(4, min(8, len(rows))):
        rows[i]["phash"] = 0x1111111111111111
    return {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "input_rows": len(features),
        "fetched": len(rows),
        "clustered": sum(1 for r in rows if "phash" in r),
        "clusters": _cluster([r for r in rows if "phash" in r]),
        "no_image": no_image[:50],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path,
                    default=ROOT / "data/properties/canonical_properties.geojson")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "data/properties/image_clusters.json")
    ap.add_argument("--max-rows", type=int, default=500,
                    help="cap on how many images to fetch (network-bound)")
    ap.add_argument("--mock", action="store_true",
                    help="skip network and use deterministic phash fixtures")
    args = ap.parse_args(argv)

    if not args.input.exists():
        sys.exit(f"input not found: {args.input}")
    feats = (json.loads(args.input.read_text()).get("features") or [])

    if args.mock:
        payload = _mock_run(feats, limit=args.max_rows)
    else:
        rows, no_image = _hash_features(feats, limit=args.max_rows)
        ok, fail = _fetch_phash(rows)
        clusters = _cluster(ok)
        payload = {
            "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "input_rows": len(feats),
            "fetched": len(rows),
            "clustered": len(ok),
            "fetch_failures": len(fail),
            "clusters": clusters,
            "no_image": no_image[:50],
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK image_dedup: {payload['input_rows']:,} rows → "
          f"{payload.get('fetched', 0):,} fetched, "
          f"{len(payload['clusters'])} clusters, "
          f"{len(payload['no_image'])} no-image")


if __name__ == "__main__":
    main()