"""
tools/build_price_surface.py — Hedonic kriging → $/ha raster (Phase 2 stub).

Per-departamento Ordinary Kriging (pykrige) + national correlogy blend.

Run:
    python3 -m tools.build_price_surface --apply
    python3 -m tools.build_price_surface --dept Central --apply
    python3 -m tools.build_price_surface --eval           # k-fold CV

Class-level technique: see
  `../docs/operations/price-model.md`
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def build_surface(dept: str | None, dry_run: bool = True) -> None:
    print(f"  [build_price_surface] STUB dept={dept or 'ALL'}, dry_run={dry_run}")


def eval_loocv(dept: str | None) -> None:
    print(f"  [build_price_surface] LOOCV STUB dept={dept or 'ALL'}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Hedonic kriging → $/ha raster (Phase 2 stub).")
    parser.add_argument("--dept", default=None, help="One departamento, or None for all.")
    parser.add_argument("--apply", action="store_true", help="Actually build. Default is dry-run.")
    parser.add_argument("--eval", action="store_true", help="Run leave-one-out CV instead.")
    args = parser.parse_args(argv)
    if args.eval:
        eval_loocv(args.dept)
    else:
        build_surface(args.dept, dry_run=not args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
