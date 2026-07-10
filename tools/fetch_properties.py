"""
tools/fetch_properties.py — Listings scraper (Phase 2 stub).

Multi-portal scraper implementing `docs/ethics/scraper-policy.md`.

Current scope: stubbed. Phase 2 implements per-portal adapters.

Run:
    python3 -m tools.fetch_properties --portal infocasas --dry-run
    python3 -m tools.fetch_properties --portal all --apply --snapshots-dir data/properties/snapshots

Class-level technique: see
  ~/.hermes/skills/ethical-web-scraping-decision
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def fetch_one_portal(portal: str, dry_run: bool = True) -> int:
    """Stub — Phase 2 implements. Returns count of listings fetched."""
    print(f"  [fetch_properties] STUB for portal={portal}, dry_run={dry_run}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Listings scraper (Phase 2 stub).")
    parser.add_argument("--portal", default="all", choices=["infocasas", "propiedades", "baiker", "all"])
    parser.add_argument("--apply", action="store_true", help="Actually fetch. Default is dry-run.")
    parser.add_argument("--snapshots-dir", default="data/properties/snapshots",
                        help="Raw snapshot output dir (gitignored).")
    args = parser.parse_args(argv)

    portals = ["infocasas", "propiedades", "baiker"] if args.portal == "all" else [args.portal]
    for p in portals:
        fetch_one_portal(p, dry_run=not args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
