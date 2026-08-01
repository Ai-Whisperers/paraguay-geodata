#!/usr/bin/env python3
"""scripts/build_inbio_zafra_strip.py

Reads data/properties/inbio_series.json (the per-PDF parser output) and
emits exports/web/data/inbio_zafra_strip.json with:

  * The 5 most-recent zafras sorted by year
  * Per-crop totals per zafra
  * Per-depto totals per zafra
  * Top-3 deptos per crop in the most-recent zafra

Usage
-----
    python3 -m scripts.build_inbio_zafra_strip
    python3 -m scripts.build_inbio_zafra_strip --input … --output …
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sort_key(year: str) -> int:
    """`2025/2026` -> 2025 for sorting."""
    try:
        return int(year.split("/")[0])
    except Exception:
        return 0


def build(series: dict) -> dict:
    zafras = sorted(series.get("zafras") or [], key=lambda z: _sort_key(z.get("year", "")))
    # Keep the last 5
    zafras = zafras[-5:]
    out_zafras: list[dict] = []
    for z in zafras:
        crops_in: dict = z.get("crops") or {}
        per_crop_totals: dict[str, float] = {}
        per_depto_totals: dict[str, float] = collections.defaultdict(float)
        for crop, deptos in crops_in.items():
            for depto, v in deptos.items():
                cur = v.get("current_ha")
                if cur is None:
                    continue
                per_crop_totals[crop] = per_crop_totals.get(crop, 0) + cur
                per_depto_totals[depto] += cur
        out_zafras.append({
            "year": z.get("year"),
            "per_crop_total_ha": {k: round(v, 2) for k, v in per_crop_totals.items()},
            "per_depto_total_ha": {k: round(v, 2) for k, v in per_depto_totals.items()},
            "source_pdf": z.get("source_pdf"),
        })

    # Top-3 deptos per crop in the most-recent zafra.
    top_by_crop: dict[str, list[dict]] = {}
    if zafras:
        last_crops = zafras[-1].get("crops") or {}
        for crop, deptos in last_crops.items():
            ranked = []
            for depto, v in deptos.items():
                cur = v.get("current_ha")
                if cur is None:
                    continue
                ranked.append({"depto": depto, "ha": round(cur, 2)})
            ranked.sort(key=lambda r: -r["ha"])
            top_by_crop[crop] = ranked[:3]

    return {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "zafras": out_zafras,
        "top_per_crop_latest_zafra": top_by_crop,
        "deptos": series.get("deptos") or [],
    }


def _synthesize_fallback() -> dict:
    """If no real series exists, return an empty envelope so the viewer can
    still load without 404.  Allows the build pipeline to be idempotent."""
    return {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "zafras": [],
        "top_per_crop_latest_zafra": {},
        "deptos": [],
        "note": "no INBIO series data — run scripts/build_inbio_series.py first",
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path,
                    default=ROOT / "data/properties/inbio_series.json")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "exports/web/data/inbio_zafra_strip.json")
    args = ap.parse_args(argv)

    if args.input.exists():
        series = json.loads(args.input.read_text())
        payload = build(series)
    else:
        payload = _synthesize_fallback()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK inbio-zafra-strip: {len(payload['zafras'])} zafras, "
          f"{len(payload['top_per_crop_latest_zafra'])} crops, "
          f"{len(payload['deptos'])} deptos")


if __name__ == "__main__":
    main()