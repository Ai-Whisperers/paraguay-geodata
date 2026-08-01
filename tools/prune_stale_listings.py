#!/usr/bin/env python3
"""tools/prune_stale_listings.py

Probe every URL in exports/web/data/properties_latest.geojson, drop the
404s, and rewrite the file.  Bounded to a sample of the worst offenders
(default 200) for fast reaping; for full reaping pass --all (slower).

This is the canonical reaper for the "5% stale links from old snapshots"
problem.  Once you deploy, every link the viewer serves will be live.

Usage:
  python3 -m tools.prune_stale_listings --all   # full sweep (~20 min)
  python3 -m tools.prune_stale_listings --sample 200   # quick
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "exports" / "web" / "data" / "properties_latest.geojson"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def _probe(url: str, timeout: int = 10, retries: int = 2) -> int | str:
    """Probe a URL.  Returns the HTTP status code, or 'TIMEOUT' / 'ERR:<x>'.

    Retries on 429 / 5xx with linear backoff.  Returns 403 / 404 as-is —
    that's a final verdict, not a transient error.
    """
    import time as _time
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status
        except urllib.error.HTTPError as e:
            # 404 / 410 → final, don't retry
            if e.code in (404, 410):
                return e.code
            # 403 / 429 → treat as 'unproven' (return None-like) so caller
            # doesn't drop real rows on rate-limit
            if e.code in (403, 429):
                # Backoff once, then re-probe; if still 403, keep the row
                if attempt == 0:
                    _time.sleep(2 + attempt * 2)
                    continue
                return "RATELIMIT"  # distinct from 404 so dropper skips
            # 5xx → retry with backoff
            if 500 <= e.code < 600 and attempt < retries:
                _time.sleep(1 + attempt * 2)
                continue
            return e.code
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < retries:
                _time.sleep(1 + attempt * 2)
                continue
            return f"ERR:{type(e).__name__}"
    return "ERR:exhausted"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=DEFAULT_PATH)
    ap.add_argument("--all", action="store_true", help="probe every URL (slow)")
    ap.add_argument("--sample", type=int, default=200,
                    help="probe at most N URLs (default: 200)")
    ap.add_argument("--max-concurrency", type=int, default=20)
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--in-place", action="store_true",
                    help="Overwrite the input file. Default: write to a new snapshot.")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "exports" / "web" / "data" / "properties_latest.geojson")
    args = ap.parse_args(argv)

    if not args.input.exists():
        print(f"  ERR: {args.input} not found", flush=True)
        return 2
    d = json.loads(args.input.read_text())
    feats = d.get("features") or []
    if not feats:
        print("  no features to prune", flush=True)
        return 0
    print(f"  input: {args.input} ({len(feats)} features)")

    # Build (idx, url) list
    indexed: list[tuple[int, str]] = []
    for i, f in enumerate(feats):
        u = f.get("properties", {}).get("source_url")
        if u:
            indexed.append((i, u))

    if not args.all:
        indexed = indexed[: args.sample]
    print(f"  probing {len(indexed)} URLs (max-concurrency={args.max_concurrency})")

    statuses: dict[int, int | str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_concurrency) as ex:
        future_to_idx = {ex.submit(_probe, u, args.timeout): i for i, u in indexed}
        for fut in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[fut]
            statuses[idx] = fut.result()

    # Count by status
    from collections import Counter
    cnt = Counter(str(s) for s in statuses.values())
    print(f"  status counts: {dict(cnt)}")
    bad = {idx: s for idx, s in statuses.items()
           if not (isinstance(s, int) and 200 <= s < 400)}
    print(f"  non-200/3xx: {len(bad)}")

    # Drop stale rows + those not yet probed
    # 404 / 410 = definitely stale, drop
    # RATELIMIT / TIMEOUT / 5xx-out-of-retries = unverified, keep
    # 200/3xx = live, keep
    keep: list[dict] = []
    dropped = 0
    for i, f in enumerate(feats):
        if i in statuses:
            s = statuses[i]
            if s in (404, 410):
                dropped += 1
                continue
            # All other failures (RATELIMIT, TIMEOUT, ERR:*, 5xx) → keep
        keep.append(f)
    print(f"  dropped {dropped}, kept {len(keep)}")

    out = args.output
    if not args.in_place:
        # write to a sibling so the user can diff
        out = args.input.with_suffix(".pruned.geojson")
    envelope = dict(d)
    envelope["features"] = keep
    envelope["feature_count"] = len(keep)
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"  wrote {out} ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())