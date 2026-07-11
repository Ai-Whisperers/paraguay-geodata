"""
tools/fetch_dncp.py — DNCP public-tender fetcher (Phase 1.5 stub).

DNCP API V3 — register at https://www.contrataciones.gov.py/datos/data
Provides: tender calls, awards, suppliers (OCDS — Open Contracting Data Standard).
Use: "what's being built in this district" overlay.

Run:
    python3 -m tools.fetch_dncp --entity calls --since 30d
    python3 -m tools.fetch_dncp --entity awards --since 90d
    python3 -m tools.fetch_dncp --entity suppliers --apply

TODO(Phase 1.5): implement against the V3 API. Pagination is per 100 records.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


ENTITIES = {
    "calls":     {"label": "Llamados (tender calls)",       "approx_per_year": 15000},
    "awards":    {"label": "Adjudicaciones (awards)",       "approx_per_year": 12000},
    "suppliers": {"label": "Proveedores (suppliers)",       "approx_per_year": 8000},
    "contracts": {"label": "Contratos (active contracts)",  "approx_per_year": 18000},
}


def fetch_entity(entity: str, since: str = "30d", dry_run: bool = True) -> int:
    if entity not in ENTITIES:
        print(f"  [fetch_dncp] ERROR: unknown entity '{entity}'. Known: {list(ENTITIES)}")
        return 0
    meta = ENTITIES[entity]
    if dry_run:
        print(f"  [fetch_dncp] STUB entity={entity} since={since}  "
              f"label={meta['label']}  approx_per_year={meta['approx_per_year']}")
    else:
        # TODO: implement V3 API pagination
        pass
    return meta["approx_per_year"]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="DNCP public-tender fetcher (Phase 1.5 stub).")
    parser.add_argument("--entity", default="calls", choices=list(ENTITIES) + ["all"])
    parser.add_argument("--since", default="30d", help="Time window: 7d, 30d, 90d, 1y.")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    dry_run = not args.apply
    entities = list(ENTITIES) if args.entity == "all" else [args.entity]
    for e in entities:
        fetch_entity(e, since=args.since, dry_run=dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))