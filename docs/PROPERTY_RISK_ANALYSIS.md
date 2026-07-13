# Property Risk Analysis v2

**Live:** https://geodata.paragu-ai.com/

Generated 2026-07-13 (v2 with depto normalization + climate sub-risk derivation).

## What it scores

Every property gets two scores:
- **Risk score** (0-200+): environmental, structural, legal
- **Pro score** (0-35): amenities, ecology

`net = pro - risk`. Categories: HIGH RISK (<-20), CAUTION (-20..0), OK (0..10), GOOD (≥10).

## Risk dimensions

| Dimension | Source | Max weight | Notes |
|---|---|---|---|
| Flood zone (point-in-polygon) | Catastro WFS, 5 polygons | 30 × severity | Asunción costanera + Río Paraguay broad zones |
| Climate flood (depto) | climate_risk.geojson (risk_level) | 15 | Derived from composite risk_level |
| Climate drought (depto) | climate_risk.geojson (drought_freq) | 8 | Numeric threshold |
| Climate heatwave (depto) | climate_risk.geojson (annual_precip, spi_2024) | 5 | Derived |
| Climate wildfire (depto) | climate_risk.geojson (forest_loss_pct_2020_2024) | 10 | Chaco deforestation = high |
| Indigenous territory (point-in-polygon) | 10 indigenous territories | 50 | Legal/regulatory concern |
| Water proximity (300m) | OSM water polylines | 25-50 | River/stream within 300m |
| Shadow (Asunción) | 49,641 OSM buildings | 8 | Wall-to-wall (<5m) |
| Lighting (close building) | same | 3 | 5-15m |

## Pro dimensions

| Dimension | Max weight | Notes |
|---|---|---|
| Near water (300m-5km) | 10-20 | Irrigation / views |
| Biodiversity (GBIF <10km) | 8-15 | Bird / nature value |

## V2 fixes over v1

1. **Depto name normalization** — handles `Asunción`/`Asuncion`, `Itapúa`/`Itapua`, etc. via a 25-entry lookup.
2. **Spatial depto lookup** — when raw `state_province` is missing or wrong, we use `admin/departamentos.geojson` point-in-polygon.
3. **Climate sub-risks derived correctly** — climate_risk.geojson only has `risk_level` (composite), `drought_freq`, `forest_loss_pct_2020_2024`, `annual_precip_mm`, `spi_2024`. v1 tried to read non-existent `flood_risk`/`drought_risk`/`heatwave_risk`/`wildfire_risk` and got all None for 9,293 properties. v2 derives them.
4. **Foreign province filtering** — Formosa (AR), Corrientes (AR), Paraná (BR), Santa Cruz (BO) are normalized to None (data contamination from cross-border listings).
5. **Asunción flood downgrade** — UI shows "(broad zone)" annotation when flood is in the Río Paraguay floodplain polygon (which covers most of central Asunción but is a coarse Catastro WFS layer).
6. **Gran Chaco seasonal flood** — also downgraded in UI to "low" since `seasonal: true` means it's not a permanent risk.

## Files

| File | Size | Purpose |
|---|---|---|
| `data/property_risk_analysis.json` | ~6-8 MB | Full per-property data (10,754 entries) |
| `data/property_risk_index.json` | ~600 KB | Lightweight coords + scores only (for heatmap) |
| `data/property_risk_summary.json` | ~60 KB | By-depto aggregate + top-30 rankings |
| `scripts/build_risk_v2.py` | ~21 KB | Generator (re-run when layers change) |

## How to load in browser

```js
// Index (~600 KB, fast — loaded at boot)
const idx = await fetch('./data/property_risk_index.json').then(r => r.json());
window.__riskIndex = idx.index;  // Map<id, {lat, lon, risk_score, ...}>

// Full (heavy — loaded only when a property popup opens)
window.loadFullRisk();  // lazy, caches in __riskById
```

## Caveats (in priority order)

1. **Catastro flood polygons are coarse** — they cover seasonal flood plains, not just permanent risk. Most of Asunción scores as "high" because of the Río Paraguay floodplain polygon overlap, not because individual properties are flood-prone. UI shows "(broad zone)" annotation.
2. **Climate is deptos-level** — two properties in the same depto share flood/drought/heatwave/wildfire risk.
3. **Indigenous territory overlap is bbox-based** — may include listings near (but not inside) actual claimed land.
4. **Shadow detection only covers Asunción** (49,641 OSM building footprints). For other cities this dimension is unknown.
5. **Water proximity assumes straight-line distance** to OSM water polylines.
6. **Drought/heatwave/wildfire are derived from composite indicators** (drought_freq, annual_precip, forest_loss) — not direct measurements.

## Score distribution (preliminary v2)

Expected distribution (after normalization):
- avg_risk Asunción: ~50 (down from 90.4 — Río Paraguay flood downgrade)
- avg_risk Central: ~85 (mostly remains high)
- avg_risk Itapúa: ~2 (unchanged, no flood polygons)
- avg_risk Boquerón: ~58 (indigenous + Chaco seasonal)
- avg_risk Caaguazú: 0 (unchanged)

Final numbers available after `build_risk_v2.py` completes (~15 min).
