"""tools/fetch_bcp_rates.py — fetch USD/PYG exchange rate from BCP.

The Banco Central del Paraguay publishes the USD/PYG reference rate daily
on their public API. The rate is what we use to mark listings as
"USD stable" (the is_usd_stable enrichment flag).

Currently this is a stub that returns a hardcoded rate (7500 PYG/USD).
The real BCP API requires authentication that we don't have access to yet.

Usage:
  python3 -m tools.fetch_bcp_rates
  python3 -m tools.fetch_bcp_rates --api-url https://...
  python3 -m tools.fetch_bcp_rates --fallback 7500

Output: data/properties/bcp_rates.json
  {
    "as_of_utc": "...",
    "pyg_per_usd": 7500,
    "pyg_per_usd_30d_avg": 7480,
    "pyg_per_usd_30d_std": 25,
    "source": "stub" | "bcp_api"
  }
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RATE_PATH = REPO / "data" / "properties" / "bcp_rates.json"

# Stub fallback rate (last known public value)
STUB_RATE = 7500


def fetch_from_api(api_url: str, api_key: str | None) -> dict | None:
    """Try to fetch from a real BCP API. Returns None on failure."""
    try:
        import urllib.request
        req = urllib.request.Request(api_url)
        if api_key:
            req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("User-Agent", "PyGeodata/1.0 (info@ai-whisperers.org)")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            # BCP returns { "pyg_per_usd": ..., "date": "..." }
            return {
                "pyg_per_usd": float(data.get("pyg_per_usd", data.get("value", 0))),
                "source": "bcp_api",
                "as_of_utc": data.get("date", datetime.datetime.utcnow().isoformat() + "Z"),
            }
    except Exception as e:
        print(f"  WARN: BCP API fetch failed: {e}")
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fetch USD/PYG exchange rate from BCP.")
    ap.add_argument("--api-url", default="",
                    help="BCP API URL (empty = use stub)")
    ap.add_argument("--api-key", default="",
                    help="BCP API key (if auth required)")
    ap.add_argument("--fallback", type=float, default=STUB_RATE,
                    help="Fallback rate when API is unavailable")
    args = ap.parse_args(argv)

    print("=== fetch_bcp_rates ===")

    as_of = datetime.datetime.utcnow().isoformat() + "Z"
    source = "stub"
    pyg_per_usd = args.fallback

    if args.api_url:
        result = fetch_from_api(args.api_url, args.api_key or None)
        if result:
            pyg_per_usd = result["pyg_per_usd"]
            source = result["source"]
            as_of = result["as_of_utc"]
            print(f"  fetched from API: {pyg_per_usd:.2f} PYG/USD")

    # Load previous 30-day average if available
    avg_30d = pyg_per_usd
    std_30d = 0
    if RATE_PATH.exists():
        try:
            prev = json.loads(RATE_PATH.read_text())
            history = prev.get("history", [])
            if history:
                recent = history[-30:]
                if recent:
                    avg_30d = sum(h["pyg_per_usd"] for h in recent) / len(recent)
                    std_30d = (sum((h["pyg_per_usd"] - avg_30d) ** 2 for h in recent) / len(recent)) ** 0.5
        except Exception:
            pass

    payload = {
        "as_of_utc": as_of,
        "pyg_per_usd": pyg_per_usd,
        "pyg_per_usd_30d_avg": round(avg_30d, 2),
        "pyg_per_usd_30d_std": round(std_30d, 2),
        "source": source,
        "history": [],  # populated by the cron
    }

    # Append to history (rolling 90-day window)
    if RATE_PATH.exists():
        prev = json.loads(RATE_PATH.read_text())
        prev_history = prev.get("history", [])
        prev_history.append({"as_of_utc": as_of, "pyg_per_usd": pyg_per_usd})
        # Keep last 90 days
        prev_history = prev_history[-90:]
        payload["history"] = prev_history
        # Recompute 30d avg/std from updated history
        recent = prev_history[-30:]
        if recent:
            avg = sum(h["pyg_per_usd"] for h in recent) / len(recent)
            std = (sum((h["pyg_per_usd"] - avg) ** 2 for h in recent) / len(recent)) ** 0.5
            payload["pyg_per_usd_30d_avg"] = round(avg, 2)
            payload["pyg_per_usd_30d_std"] = round(std, 2)

    RATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RATE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote {RATE_PATH.relative_to(REPO)}")
    print(f"  PYG/USD: {pyg_per_usd:.2f} (avg 30d: {avg_30d:.2f} ± {std_30d:.2f})")
    if source == "stub":
        print(f"  (using stub fallback {STUB_RATE} — set --api-url to enable real BCP API)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
