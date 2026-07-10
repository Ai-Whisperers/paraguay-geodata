# Price Surface Model — Operations Playbook

Turn sparse property listings + escritura anchors into a continuous price-per-hectare surface for all of Paraguay.

## Goal

Per departamento, ship:
1. A **hedonic price raster** (GeoTIFF) at 100 m/px — `$/ha` for any (lat, lon) in Paraguay
2. A **confidence band** (low/high) — kriging variance gives this free
3. A **published API**: `GET /prices.json?dept=<id>&lat=<lat>&lon=<lon>` returns `{usd_per_ha, confidence_low, confidence_high, nearest_anchor_count}`

## Data inputs

| Layer | Source | Coverage | Sample size |
|---|---|---|---|
| Listings (residential, commercial, agricultural) | `tools/fetch_properties.py` output | All PY portals | ~5,000-20,000 active at any time |
| Escrituras (transaction deeds) | `data/cadastre/escrituras/*.csv` operator-supplied | Where the operator has dealt | ~50-500 anchors initially |
| Public appraisal records | Catastro (limited public access) | Where available | 0-100 per departamento |

## Model choice: Ordinary Kriging (per departamento) + corregionalised national overlay

Why not IDW? Because IDW has no confidence band and ignores clustering.
Why not Random Forest? Because we won't have the feature coverage (house age, exact frontage, etc.) for ML until listings carry attrs.
Why not a national single kriging? Because variograms are radically different between Central/Asunción urban vs Chaco rural.

Per-departamento kriging has a problem: rural departamentos have <10 listings. The national correlogy model is a backup:

```
$/ha(raw)  =  kriging(direct listings within 100 km, variogram_per_dept)
$/ha(blend)  =  0.7 * $/ha(raw)  +  0.3 * $/ha(national variance corrected)
```

The 0.7/0.3 is a hyper-parameter; calibration happens via k-fold leave-one-out RMSE on a held-out subset of listings every 4 weeks. If the blended model beats the raw by <2% RMSE, set the 0.7/0.3 to 1.0/0.0 (degrade to per-dept kriging).

## Variogram families to try

| Family | Best for | Range |
|---|---|---|
| Exponential | Most urban Central, all rural | 5-50 km |
| Spherical | Some urban + mixing urban/rural | 5-30 km |
| Gaussian | Dense urban (Asunción barrio granularity) | 1-10 km |

Pick by **leave-one-out RMSE** per departamento, lowest wins.

## Outputs

```
data/prices/
├── departamento_<code>_raw.tif            (kriging mean, float32, 100m/px)
├── departamento_<code>_variance.tif       (kriging variance, float32, 100m/px)
├── departamento_<code>_confidence.json    {rmse_loocv, sample_count, range_used, variogram_type}
├── departamento_<code>_anchors.geojson    (the listings + escrituras used, with kriging weights)
├── national_blended.tif                   (blended kriging per above)
├── national_blend_variance.tif
├── national_confidence.json
└── eval/
    ├── <date>_loocv.json                  (per-departamento CV metrics)
    ├── <date>_rmse_chart.png               (per-departamento RMSE comparison)
    └── <date>_scatter.png                  (predicted vs actual $/ha)
```

## Validation & testing

**Leave-one-out cross-validation** is the weekly heartbeat. For each listing in the most recent snapshot:
1. Remove it from training
2. Re-krig without it
3. Predict $/ha at its (lat, lon)
4. Compute absolute error vs observed $/ha

Aggregate per-departamento:
- **Median absolute error** should be <40% of the mean $/ha (urban) or <60% (rural)
- **95th percentile absolute error** should be <100%
- **Coverage**: predictions exist for ≥95% of the territorio nacional

Failed thresholds → page operator immediately. Can't ship until thresholds met.

## Spec — `exports/web/data/price_surface.geojson`

Bbox-clipped GeoJSON for the public viewer. We **don't** ship the 100m/px raster publicly (it's huge); instead, polygonise the raster into hexagon bins at ~5 km/hex and ship ~10k features as one GeoJSON. Each hex has:

```json
{
  "type": "Feature",
  "geometry": { "hex polygon ..." },
  "properties": {
    "hex_id": "h_-57.5_-25.5",
    "centroid": [-57.5, -25.5],
    "$/ha_p50": 240000,
    "$/ha_p10": 80000,
    "$/ha_p90": 600000,
    "n_anchors_within_10km": 23,
    "model_type": "blended",
    "as_of_date": "2026-07-10"
  }
}
```

## API (later — Phase 3 if needed)

If the operator builds a paid client (e.g. an insurance/financing widget), wrap a thin API on top:

```
GET /api/v1/price?lat=-25.2637&lon=-57.5759
GET /api/v1/price?bbox=-57.6,-25.3,-57.5,-25.2
```

Wraps CF Worker + R2 storage. ~$0.05 per 1000 queries on workers paid tier; cheaper on free (100k/day free).

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Per-dept kriging sample size too small | High rural | High | Blend with national; degrade gracefully |
| Listings prices biased toward asking (vs transaction) | High | High | Escrtura anchors dominate the blend; listings are priors |
| Portal listings include stale "asking" prices | High | Med | Cross-reference with escritura anchors; freshness flag |
| Operator-resistance to listing scraping | Med | High | Ethics gate; respect ToS; PII redaction |
| FX rate volatility for PYG-denominated listings | Med | Low | Refresh FX at scrape time; store both USD + PYG |
| Kriging doesn't fit Chaco livestock pricing | High | Med | Chaco rural may need a separate model (per-dept with different variogram) |

## Why this isn't ML

Until we have property-level attributes (year built, surface, frontage, etc.), a hedonic model won't outperform kriging. Phase 4 (not in current plan) might add `attrs.bedrooms × district` index + gradient-boosted regressor. Phase 2/3 stick with kriging because it's:
- Deterministic (no training-time surprises)
- Confidence-banded (output variance tells you where trust is low)
- $0 to compute (vs ML training infra)
- Explainable to the operator

When your AI agents or staff can build kriging in 20 lines (pykrige), you don't need ML until kriging's RMSE ceiling becomes the bottleneck.
