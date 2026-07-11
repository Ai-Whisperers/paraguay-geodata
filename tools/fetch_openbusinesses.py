"""
tools/fetch_openbusinesses.py — Open business registries (Phase 2 stub).

Three sources combined:
  MIC — Ministerio de Industria y Comercio (maquila + industry census)
  SET — Subsecretaría de Tributación (RUC lookup)
  UIP — Unión Industrial Paraguaya (member directory)
  AHK — German-Paraguayan Chamber (member directory)

Each has a public member directory / registry that's browsable. We aggregate
into a single "active businesses" GeoJSON.

Run:
    python3 -m tools.fetch_openbusinesses --source all --dry-run
    python3 -m tools.fetch_openbusinesses --source mic --apply
    python3 -m tools.fetch_openbusinesses --ruc <number>      # single RUC lookup (SET)

TODO(Phase 2): implement. MIC and AHK are Cloudflare-protected; need headless
Chrome per the paraguay-research-toolkit skill. UIP member directory is
browse-friendly.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


SOURCES = {
    "mic": {"label": "MIC (Ministerio de Industria y Comercio)", "approx": 4500,  "phase": "2"},
    "set": {"label": "SET (RUC registry)",                        "approx": 90000, "phase": "2"},
    "uip": {"label": "UIP (Unión Industrial Paraguaya)",          "approx": 250,   "phase": "2"},
    "ahk": {"label": "AHK Paraguay (German chamber)",             "approx": 350,   "phase": "2"},
}


def fetch_source(source: str, dry_run: bool = True) -> int:
    if source not in SOURCES:
        print(f"  [fetch_openbusinesses] ERROR: unknown source '{source}'")
        return 0
    meta = SOURCES[source]
    if dry_run:
        print(f"  [fetch_openbusinesses] STUB source={source}  "
              f"label={meta['label']}  approx={meta['approx']}  phase={meta['phase']}")
    return 0


def ruc_lookup(ruc: str, dry_run: bool = True) -> dict:
    if dry_run:
        print(f"  [fetch_openbusinesses] STUB RUC lookup for '{ruc}'")
    return {"ruc": ruc, "status": "stub", "phase": "2"}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Open business registries (Phase 2 stub).")
    parser.add_argument("--source", default="all", choices=list(SOURCES) + ["all"])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--ruc", default=None, help="Single RUC lookup against SET.")
    args = parser.parse_args(argv)
    dry_run = not args.apply

    if args.ruc:
        result = ruc_lookup(args.ruc, dry_run=dry_run)
        print(result)
        return 0

    sources = list(SOURCES) if args.source == "all" else [args.source]
    for s in sources:
        fetch_source(s, dry_run=dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))