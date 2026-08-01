#!/usr/bin/env python3
"""tools/build_fair_price_model_v2.py

Per-depto Ridge regression trained on the canonical properties artifact.
Replaces the v1 model (R² ≈ 0.017 — decorative) with v2 that:

  * Trains ONLY on rows where quality_flags does NOT contain
    currency_conflict or area_conflict (drops the 4,747+ noisy rows).
  * Uses Ridge (alpha=1.0) per depto so deptos with few listings still get
    a sensible prior.
  * Includes the canonical 22-feature enum as binary indicators.
  * Reports R² and MAE per depto so we can see which deptos actually
    have a model that works.

Output: data/properties/fair_price_model_v2.json (also mirrored to
         exports/web/data/ml/fair_price_model_v2.json so the viewer can
         load it via the same path as v1).

Usage
-----
    python3 -m tools.build_fair_price_model_v2
    python3 -m tools.build_fair_price_model_v2 --input … --output-dir …
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Required sklearn
try:
    import numpy as np
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_absolute_error, r2_score
except ImportError:  # pragma: no cover
    sys.exit("scikit-learn required: pip install scikit-learn")

FEATURE_COLS = ["area_ha", "bedrooms", "bathrooms", "parking_spaces"]
FEATURE_ENUM_KEY = "canonical_features"


def _row_to_xy(p: dict) -> tuple[list[float] | None, float | None]:
    """Map a single property to (X, y).  Returns None when unusable."""
    flags = set(p.get("quality_flags") or [])
    if "currency_conflict" in flags or "area_conflict" in flags:
        return None, None
    if p.get("listing_type") and p["listing_type"] != "sale":
        return None, None
    y = p.get("price_usd")
    if not y or not isinstance(y, (int, float)) or y <= 0:
        return None, None
    x: list[float] = []
    for k in FEATURE_COLS:
        v = p.get(k)
        x.append(float(v) if isinstance(v, (int, float)) and v >= 0 else 0.0)
    feats = set(p.get(FEATURE_ENUM_KEY) or [])
    for f in sorted(_feature_enum()):
        x.append(1.0 if f in feats else 0.0)
    return x, float(y)


def _feature_enum() -> set[str]:
    """Discover the canonical feature enum from the artifacts (or hard-coded
    fallback if facets are unavailable)."""
    facets_path = ROOT / "data/properties/facets.json"
    if facets_path.exists():
        try:
            d = json.loads(facets_path.read_text())
            return {f["value"] for f in d.get("facets", {}).get("features", [])}
        except Exception:
            pass
    return {
        "pool", "bbq", "bbqArea", "garden", "balcony", "terrace",
        "parking", "security", "airConditioning", "heating",
        "furnished", "equippedKitchen", "laundry", "internet",
        "cableTV", "elevator", "gym", "eventRoom", "modern", "new",
        "builtInClosets", "solarPanels",
    }


def _build_per_depto(features: list[dict]) -> dict:
    by_depto: dict[str, list[tuple[list[float], float]]] = collections.defaultdict(list)
    skipped = 0
    for f in features:
        p = (f.get("properties") or {})
        x, y = _row_to_xy(p)
        if x is None or y is None:
            skipped += 1
            continue
        depto = p.get("state_province") or "_unknown_"
        by_depto[depto].append((x, y))

    out: dict[str, dict] = {}
    global_rows: list[tuple[list[float], float]] = []
    for depto, rows in by_depto.items():
        global_rows.extend(rows)
        n = len(rows)
        if n < 10:
            out[depto] = {
                "n_train": n,
                "r2": None, "mae_usd": None,
                "note": "too_few_rows_for_per_depto_model",
            }
            continue
        X = np.array([r[0] for r in rows], dtype=float)
        y = np.array([r[1] for r in rows], dtype=float)
        model = Ridge(alpha=1.0, random_state=42)
        model.fit(X, y)
        pred = model.predict(X)
        r2 = float(r2_score(y, pred))
        mae = float(mean_absolute_error(y, pred))
        coefs = {col: float(c) for col, c in zip(FEATURE_COLS + sorted(_feature_enum()), model.coef_)}
        out[depto] = {
            "n_train": n,
            "r2": round(r2, 3),
            "mae_usd": round(mae, 2),
            "intercept": float(model.intercept_),
            "coefficients": coefs,
        }

    # Global fallback (used when a depto is missing from `out`).
    rows = global_rows
    if len(rows) >= 10:
        X = np.array([r[0] for r in rows], dtype=float)
        y = np.array([r[1] for r in rows], dtype=float)
        model = Ridge(alpha=1.0, random_state=42)
        model.fit(X, y)
        pred = model.predict(X)
        out["_global_"] = {
            "n_train": len(rows),
            "r2": round(float(r2_score(y, pred)), 3),
            "mae_usd": round(float(mean_absolute_error(y, pred)), 2),
            "intercept": float(model.intercept_),
            "coefficients": {
                col: float(c) for col, c in zip(FEATURE_COLS + sorted(_feature_enum()), model.coef_)
            },
        }
    return {
        "per_depto": out,
        "skipped_quality_or_unusable": skipped,
        "feature_columns": FEATURE_COLS,
        "feature_enum": sorted(_feature_enum()),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path,
                    default=ROOT / "data/properties/canonical_properties.geojson")
    ap.add_argument("--output-dir", type=Path, default=ROOT / "data/properties")
    ap.add_argument("--mirror", type=Path,
                    default=ROOT / "exports/web/data/ml/fair_price_model_v2.json")
    args = ap.parse_args(argv)
    if not args.input.exists():
        sys.exit(f"input not found: {args.input}")
    feats = json.loads(args.input.read_text()).get("features") or []
    result = _build_per_depto(feats)

    envelope = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "input_rows": len(feats),
        **result,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out = args.output_dir / "fair_price_model_v2.json"
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.mirror:
        args.mirror.parent.mkdir(parents=True, exist_ok=True)
        args.mirror.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")

    # Summary
    deptos_with_r2 = [d for d, v in result["per_depto"].items() if v.get("r2") is not None and d != "_global_"]
    rs = [result["per_depto"][d]["r2"] for d in deptos_with_r2]
    print(f"OK fair-price v2: {len(feats):,} rows → "
          f"{len(deptos_with_r2)} deptos with R², "
          f"{result['skipped_quality_or_unusable']:,} skipped, "
          f"global R²={result['per_depto'].get('_global_', {}).get('r2', 'n/a')}, "
          f"median depto R²={statistics.median(rs) if rs else 'n/a'}")
    print(f"  output    {out}")
    print(f"  mirror    {args.mirror}")


if __name__ == "__main__":
    main()