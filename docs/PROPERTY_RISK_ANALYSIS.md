# Property Risk Analysis

**Live:** https://geodata.paragu-ai.com/

Generated 2026-07-13. 10,754 properties scored against 7 environmental + structural risk layers.

## What's scored

Each property gets two parallel scores (0-200+ range):

### Risk score (0-200+)
- **Flood zone** (Catastro WFS, 5 polygons): 0-30 per zone, weighted by `severity` field
- **Climate (depto-level)**: flood / drought / heatwave / wildfire from `climate_risk.geojson`
  - high: ×2, medium: ×1, low: ×0.3
- **Indigenous territory** (10 polygons): +50 if point-in-polygon
- **Water proximity** (river/stream within 300m): 25-50
- **Shadow** (wall-to-wall building in Asunción, 49,641 footprints): +8
- **Lighting** (close building 5-15m): +3

### Pro score (0-35)
- **Near water** (300m - 5km): +10-20
- **Biodiversity** (GBIF observation within 10km): +8-15

### Net score
`pro_score - risk_score`. Bucketed as:
- `net < -20`: HIGH RISK
- `-20 ≤ net < 0`: CAUTION
- `0 ≤ net < 10`: OK
- `net ≥ 10`: GOOD

## How the score is computed

```
risk_score = (
    flood_zone_severity * 30 +
    climate_flood * 15 +
    climate_drought * 8 +
    climate_heatwave * 5 +
    climate_wildfire * 10 +
    indigenous_territory * 50 +
    water_close_severity * 25 +
    shadow * 8 +
    lighting * 3
)
```

The current dataset averages:
- 78% of properties are in a flood zone (Catastro WFS layer is broad — includes seasonal flood plains, not just permanent risk)
- 1.2% are in indigenous territories
- 0.3% have wall-to-wall buildings (Asunción only)
- 73% are within 5km of a water body
- 87% have GBIF biodiversity observations within 10km

## How it's surfaced in the UI

1. **Property popup** — risk + pro score chip with severity, plus an itemized list of issues
2. **Sidebar "Selected property analysis"** — same data, separate panel that persists while popup closes
3. **Heatmap · risk score** — visualize the spatial distribution of risk
4. **`/data/property_risk_summary.json`** — by-depto aggregate + top-30 riskiest + top-30 highest-pro

## Files

| File | Size | Purpose |
|---|---|---|
| `data/property_risk_analysis.json` | ~2-3 MB | Per-property full analysis (10,754 entries) |
| `data/property_risk_summary.json` | ~50 KB | Aggregate stats + rankings |
| `scripts/build_risk_fast.py` | 12 KB | Generator script (re-run when layers change) |

## Caveats

- **Climate is deptos-level**, not point-level. Two properties in the same depto share flood/drought/heatwave/wildfire risk.
- **Indigenous territories are point-in-polygon**. Some listings are in the approximate bbox of a territory; this is a strong negative signal but the bbox may be wider than the actual claimed land.
- **Wall-to-wall detection only covers Asunción** (49,641 OSM building footprints). For other cities this dimension is unknown.
- **Water proximity assumes straight-line distance** to OSM water polylines; actual flood propagation depends on terrain and infrastructure.

## How to re-run

```bash
cd /root/paraguay-geodata
python3 scripts/build_risk_fast.py
python3 -c "import json; d = json.load(open('exports/web/data/property_risk_analysis.json')); print(len(d['analyses']), 'analyses')"
```

Takes ~10 minutes on a single thread. Could be parallelized to 2-3 minutes with multiprocessing if needed.
