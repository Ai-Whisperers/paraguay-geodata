#!/usr/bin/env python3
"""tools/build_fair_price_model.py

Train a lightweight fair-price model for Paraguayan properties.
Predicts $/ha from lat/lon + property_type + listing_type + bedrooms +
area buckets. Used to flag overpriced/underpriced listings in the UI.

Output: exports/web/data/ml/fair_price_model.json
{
  "as_of": "2026-07-11",
  "model_version": "1.0",
  "training_samples": 5432,
  "feature_columns": ["lat", "lon", "type_casa", "type_terreno", "listing_sale", "listing_rent", "beds", "area_ha"],
  "buckets": {
    "depto_price_model": { "Central": { "intercept": 5000, "coefs": {"lat": 100, "lon": -50, ...}, "r2": 0.42, "samples": 200 } }
  },
  "fallback_global": { "intercept": 5000, "coefs": {...}, "r2": 0.31, "samples": 5432 }
}

Usage:
  python3 tools/build_fair_price_model.py
"""
import json
import math
import statistics
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('/root/paraguay-geodata')
PROPERTIES = ROOT / 'exports/web/data/properties_latest.geojson'
OUT = ROOT / 'exports/web/data/ml/fair_price_model.json'


def simple_linear_regression(xs, ys):
    """Closed-form OLS. Returns (intercept, slope, r2)."""
    n = len(xs)
    if n < 2:
        return 0, 0, 0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        return mean_y, 0, 0
    slope = num / den
    intercept = mean_y - slope * mean_x
    ss_res = sum((ys[i] - (intercept + slope * xs[i])) ** 2 for i in range(n))
    ss_tot = sum((ys[i] - mean_y) ** 2 for i in range(n))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return intercept, slope, max(0, r2)


def main() -> int:
    data = json.load(open(PROPERTIES))
    features = data.get('features', [])
    print(f'Total features: {len(features)}')

    # Compute $/ha for each (use feature $ if missing)
    samples = []
    for f in features:
        p = f.get('properties') or {}
        if not p.get('price_usd') or not p.get('area_ha'):
            continue
        if p['price_usd'] <= 0 or p['area_ha'] <= 0:
            continue
        per_ha = p['price_usd'] / p['area_ha']
        if per_ha < 1 or per_ha > 1e10:  # sanity
            continue
        coords = (f.get('geometry') or {}).get('coordinates')
        if not coords:
            continue
        lon, lat = coords[0], coords[1]
        samples.append({
            'lat': lat,
            'lon': lon,
            'per_ha': per_ha,
            'log_per_ha': math.log10(max(1, per_ha)),
            'type': p.get('property_type', 'unknown'),
            'listing': p.get('listing_type', 'sale'),
            'beds': p.get('bedrooms') or 0,
            'area_ha': p['area_ha'],
            'depto': p.get('state_province') or 'Unknown',
        })

    print(f'Valid samples: {len(samples)}')

    # Per-depto model: separate linear regressions
    by_depto = {}
    for s in samples:
        by_depto.setdefault(s['depto'], []).append(s)

    depto_models = {}
    for depto, items in by_depto.items():
        if len(items) < 30:  # need min 30 samples
            continue
        # Features: log(area_ha), lat, lon, beds
        xs_area = [math.log10(max(0.01, s['area_ha'])) for s in items]
        ys = [s['log_per_ha'] for s in items]
        # Multi-feature via successive OLS
        intercept1, slope1, r2_1 = simple_linear_regression(xs_area, ys)
        # Residuals + lat
        residuals1 = [ys[i] - (intercept1 + slope1 * xs_area[i]) for i in range(len(ys))]
        intercept2, slope2, r2_2 = simple_linear_regression([s['lat'] for s in items], residuals1)
        # Add lon
        residuals2 = [residuals1[i] - (intercept2 + slope2 * items[i]['lat']) for i in range(len(ys))]
        intercept3, slope3, r2_3 = simple_linear_regression([s['lon'] for s in items], residuals2)
        # Add beds
        residuals3 = [residuals2[i] - (intercept3 + slope3 * items[i]['lon']) for i in range(len(ys))]
        beds_filtered = [(s['beds'], r) for s, r in zip(items, residuals3) if s['beds'] > 0]
        if beds_filtered:
            xs_beds = [b[0] for b in beds_filtered]
            ys_beds = [b[1] for b in beds_filtered]
            intercept4, slope4, r2_4 = simple_linear_regression(xs_beds, ys_beds)
        else:
            intercept4, slope4, r2_4 = 0, 0, 0
        depto_models[depto] = {
            'intercept': intercept1 + intercept2 + intercept3 + intercept4,
            'coefs': {
                'log_area': slope1,
                'lat': slope2,
                'lon': slope3,
                'beds': slope4,
            },
            'r2': r2_3,
            'samples': len(items),
            'mean_per_ha': statistics.mean(s['per_ha'] for s in items),
            'median_per_ha': statistics.median(s['per_ha'] for s in items),
        }

    # Global fallback model (all samples)
    xs_area_all = [math.log10(max(0.01, s['area_ha'])) for s in samples]
    ys_all = [s['log_per_ha'] for s in samples]
    i_g, sl_g, r2_g = simple_linear_regression(xs_area_all, ys_all)

    out = {
        'as_of': datetime.now(timezone.utc).isoformat(),
        'model_version': '1.0',
        'algorithm': 'piecewise linear regression per depto',
        'training_samples': len(samples),
        'global_stats': {
            'mean_per_ha': statistics.mean(s['per_ha'] for s in samples),
            'median_per_ha': statistics.median(s['per_ha'] for s in samples),
            'p25_per_ha': statistics.quantiles([s['per_ha'] for s in samples], n=4)[0] if len(samples) > 4 else 0,
            'p75_per_ha': statistics.quantiles([s['per_ha'] for s in samples], n=4)[2] if len(samples) > 4 else 0,
        },
        'feature_columns': ['log_area', 'lat', 'lon', 'beds'],
        'depto_models': depto_models,
        'global_fallback': {
            'intercept': i_g,
            'coefs': {'log_area': sl_g, 'lat': 0, 'lon': 0, 'beds': 0},
            'r2': r2_g,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))

    print(f'Wrote {OUT}')
    print(f'  Deptos with 30+ samples: {len(depto_models)}')
    print(f'  Mean R²: {sum(m["r2"] for m in depto_models.values()) / max(1, len(depto_models)):.3f}')
    print(f'  Global mean $/ha: ${out["global_stats"]["mean_per_ha"]:,.0f}')
    print(f'  Global median $/ha: ${out["global_stats"]["median_per_ha"]:,.0f}')

    # Save a sample of predictions for verification
    sample_predictions = []
    for s in samples[:50]:
        model = depto_models.get(s['depto'])
        if model:
            pred_log = (
                model['intercept'] +
                model['coefs']['log_area'] * math.log10(max(0.01, s['area_ha'])) +
                model['coefs']['lat'] * s['lat'] +
                model['coefs']['lon'] * s['lon'] +
                model['coefs']['beds'] * (s['beds'] if s['beds'] > 0 else 0)
            )
            pred_per_ha = 10 ** pred_log
            ratio = s['per_ha'] / pred_per_ha
            sample_predictions.append({
                'depto': s['depto'],
                'actual_per_ha': round(s['per_ha']),
                'predicted_per_ha': round(pred_per_ha),
                'ratio': round(ratio, 2),
            })
    print('\nSample predictions:')
    for p in sample_predictions[:10]:
        flag = '🔥' if p['ratio'] > 2 else '💰' if p['ratio'] < 0.5 else '  '
        print(f'  {flag} {p["depto"][:15]:15s} actual=${p["actual_per_ha"]:>10,.0f}  pred=${p["predicted_per_ha"]:>10,.0f}  ratio={p["ratio"]:.2f}x')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())