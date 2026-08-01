#!/usr/bin/env python3
"""tools/check_property_links.py (extended)

Probes source URLs and prints any 4xx/5xx for triage.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

USER_AGENT = "paraguay-geodata/0.1 (+github.com/Ai-Whisperers/paraguay-geodata)"


def _check(url: str, timeout: int):
    try:
        req = urllib.request.Request(url, method="GET", headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/json",
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return url, r.status
    except urllib.error.HTTPError as e:
        return url, e.code
    except Exception:
        return url, 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path,
                    default=ROOT / "exports/web/data/properties_latest.geojson")
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--max-concurrency", type=int, default=10)
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--per-source", action="store_true")
    args = ap.parse_args(argv)

    raw = json.loads(args.input.read_text())
    feats = raw.get("features") or []

    if args.per_source:
        by_src: dict[str, list[str]] = collections.defaultdict(list)
        for f in feats:
            p = f.get("properties") or {}
            u = p.get("source_url")
            if u:
                by_src[p.get("source") or "?"].append(u)
        per = max(1, args.samples // max(1, len(by_src)))
        sample_urls = []
        for urls in by_src.values():
            sample_urls.extend(urls[:per])
    else:
        sample_urls = [f["properties"]["source_url"] for f in feats
                       if f.get("properties", {}).get("source_url")][:args.samples]

    results = []
    with ThreadPoolExecutor(max_workers=args.max_concurrency) as ex:
        futs = {ex.submit(_check, u, args.timeout): u for u in sample_urls}
        for fut in as_completed(futs):
            results.append(fut.result())

    by_status = collections.Counter()
    for _, st in results:
        by_status[st] += 1

    print(f"probed {len(results)} URLs")
    print(f"status histogram: {dict(sorted(by_status.items()))}")
    ok = sum(1 for _, st in results if 200 <= st < 400)
    fail = sum(1 for _, st in results if st == 0 or st >= 400)
    print(f"  reachable (2xx/3xx): {ok}/{len(results)} = {ok/len(results)*100:.1f}%")
    print(f"  failed: {fail}/{len(results)} = {fail/len(results)*100:.1f}%")

    # Show all failures (3xx is fine, 4xx/5xx + 0 is broken)
    bad = [(u, st) for u, st in results if st == 0 or st >= 400]
    if bad:
        print(f"\nfailures ({len(bad)}):")
        for u, st in bad[:25]:
            print(f"  HTTP {st if st else 'TIMEOUT'}: {u}")

    # Per-source breakdown
    by_src = collections.Counter()
    by_src_ok = collections.Counter()
    for u, st in results:
        # extract source from URL host
        host = u.split("/")[2] if "://" in u else "?"
        by_src[host] += 1
        if 200 <= st < 400:
            by_src_ok[host] += 1
    print("\nper-host:")
    for h, n in by_src.most_common():
        ok = by_src_ok.get(h, 0)
        print(f"  {h:>30s}: {ok}/{n} OK = {ok/n*100:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())