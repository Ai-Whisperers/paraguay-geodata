"""tools/webhook_ingest.py

Lightweight server-side webhook ingestion for client-side events.

The site posts JS errors / vital metrics / checkout attempts to
/api/v1/vitals.  CF Pages static hosting can't run a real server,
but we can ingest them locally and merge into the bulletin.

Approach:
  - Client posts to /api/v1/vitals (handled by CF Pages _redirects).
  - We also accept posts to tools/webhook_ingest.py when running locally
    or behind the cron: it appends each event to data/properties/events.jsonl
    and emits a daily summary to exports/web/data/vitals_summary.json.

Output:
  /data/properties/events.jsonl (one JSON event per line)
  /exports/web/data/vitals_summary.json (5-minute rolling summary)

Usage:
  python3 -m tools.webhook_ingest --serve 8080  # local-only HTTP server
  python3 -m tools.webhook_ingest --summarize    # rebuild the summary file
"""
from __future__ import annotations

import argparse
import collections
import http.server
import json
import os
import socketserver
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "properties" / "events.jsonl"
SUMMARY_PATH = ROOT / "exports" / "web" / "data" / "vitals_summary.json"


def _append_event(event: dict) -> None:
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _load_events(within_minutes: int = 60) -> list[dict]:
    """Return events captured in the last `within_minutes`."""
    if not EVENTS_PATH.exists():
        return []
    cutoff = time.time() - within_minutes * 60
    out = []
    for line in EVENTS_PATH.read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = e.get("ts", 0) / 1000  # milliseconds to seconds
        if ts >= cutoff:
            out.append(e)
    return out


def summarize() -> dict:
    """Build a 5-minute rolling summary and write it."""
    events = _load_events(within_minutes=60)
    by_type = collections.Counter()
    by_rating = collections.Counter()
    pages = collections.Counter()
    for e in events:
        by_type[e.get("type", "?")] += 1
        if e.get("rating"):
            by_rating[e.get("rating")] += 1
        if e.get("url"):
            path = e["url"].split("?")[0].split("/")[-1] or "index"
            pages[path] += 1

    summary = {
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        "window_minutes": 60,
        "total_events": len(events),
        "by_type": dict(by_type),
        "by_rating": dict(by_rating),
        "top_pages": pages.most_common(10),
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"  wrote {SUMMARY_PATH}: {summary['total_events']} events")
    return summary


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/v1/vitals":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="ignore")
        try:
            event = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return
        event.setdefault("ts", int(time.time() * 1000))
        event.setdefault("url", "/")
        event["received_at"] = datetime.now(timezone.utc).isoformat()
        _append_event(event)
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):  # noqa: A002
        # Quiet by default — uncomment for debugging
        # sys.stderr.write("%s - - %s\n" % (self.address_string(), format % args))
        pass


def serve(port: int = 8080) -> int:
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), _Handler) as httpd:
        print(f"  webhook_ingest listening on 127.0.0.1:{port}")
        httpd.serve_forever()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--serve", type=int, default=None, metavar="PORT",
                    help="Start a local HTTP server (useful for testing).")
    ap.add_argument("--summarize", action="store_true",
                    help="Rebuild the vitals_summary.json from the events log.")
    args = ap.parse_args(argv)
    if args.summarize:
        summarize()
        return 0
    if args.serve is not None:
        return serve(args.serve)
    ap.error("specify --serve PORT or --summarize")


if __name__ == "__main__":
    sys.exit(main())
