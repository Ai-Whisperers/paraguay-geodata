"""
tools/fetch_inbio.py — INBIO agricultural surfaces + yield (Phase 1.5 stub).

INBIO publishes per-zafra crop reports (soja, maíz, trigo, girasol, etc.) with
per-departamento area + yield statistics derived from satellite imagery.

URL: https://inbio.org.py/superficies-de-siembra/
Zafra: Sep-Jun (soja) + zafriña (winter)
Format: PDF reports + occasional GeoTIFF supplements

Run:
    python3 -m tools.fetch_inbio --crop soja --zafra 2024-2025
    python3 -m tools.fetch_inbio --crop all --apply

TODO(Phase 1.5): implement. The reports are PDF; need PDFPlumber or
pdfplumber + spatial joining by departamento code.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


CROPS = {
    "soja":      {"label": "Soja",       "approx_ton_year": 9_300_000},
    "maiz":      {"label": "Maíz",       "approx_ton_year": 5_500_000},
    "trigo":     {"label": "Trigo",      "approx_ton_year": 1_200_000},
    "girasol":   {"label": "Girasol",    "approx_ton_year": 250_000},
    "sesamo":    {"label": "Sésamo",     "approx_ton_year": 35_000},
    "arroz":     {"label": "Arroz",      "approx_ton_year": 800_000},
    "canola":    {"label": "Canola",     "approx_ton_year": 80_000},
    "kaa_hehe":  {"label": "Ka'a he'ê",  "approx_ton_year": 1_200},  # stevia (small specialty)
}


def fetch_crop(crop: str, zafra: str = "2024-2025", dry_run: bool = True) -> int:
    if crop not in CROPS:
        print(f"  [fetch_inbio] ERROR: unknown crop '{crop}'. Known: {list(CROPS)}")
        return 0
    meta = CROPS[crop]
    if dry_run:
        print(f"  [fetch_inbio] STUB crop={crop} zafra={zafra}  "
              f"label={meta['label']}  approx_ton={meta['approx_ton_year']:,}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="INBIO crop area + yield (Phase 1.5 stub).")
    parser.add_argument("--crop", default="soja", choices=list(CROPS) + ["all"])
    parser.add_argument("--zafra", default="2024-2025", help="Zafra year (Sep-Jun range).")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    dry_run = not args.apply
    crops = list(CROPS) if args.crop == "all" else [args.crop]
    for c in crops:
        fetch_crop(c, zafra=args.zafra, dry_run=dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))