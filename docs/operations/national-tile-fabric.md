# National Tile Fabric — Operations Playbook

The phased rollout plan for `Ai-Whisperers/paraguay-geodata`.

## Why a tile fabric

Paraguay is 406,752 km². Building every data layer over the whole country in one shot would be:
1. Slow — Esri HD + Sentinel-2 + MapBiomas fetch alone = ~80-100 GB of raw data, weeks of CPU.
2. Wasteful — most of the Chaco has very low demand; near-zero listings.
3. Hard to verify — the per-tile unit can be smoke-tested in 30 seconds; the country can't be smoke-tested at all.

Tile fabric = a grid of small, independent units of reproducibility. Each tile is its own pipeline run; one tile can fail without breaking the deploy; optimisation can target busy tiles first.

## Tile size choice: 10×10 km

| Option | Pros | Cons | Decision |
|---|---|---|---|
| **10×10 km** (LQV-proven) | Already stress-tested viewer at this scale; Cerros/streams algorithms tuned to it; Landsat/MapBiomas tiles intersect cleanly | ~7,900 tiles covering full country | **Chosen** |
| 5×5 km | Finer zoom granularity | 4× more tiles (~31,600); no viewer benefit unless we ship a tile-pyramid; same fetch cost per km² | Rejected |
| 20×20 km | Fewer tiles (~2,000) | Doesn't match what the viewer renders natively; viewer would need per-tile adaptors | Rejected |

## Tile counts (Phase 0 reference)

| Subset | Count | Coverage |
|---|---|---|
| All Paraguay | 7,912 | 100% of the bbox |
| 20-city urban anchors (3×3 = 9 tiles each) | 153 (~85 unique centres + neighbours) | ~2% of country by area, ~70% by population |
| LQV reference tile | 1 | The Paraguarí 10×10 box we already have |

(Tile index regenerates from scratch in `tools/national_tile_index.py` — current numbers above as of 2026-07-10.)

## Phase 0 — Skeleton

**Status**: 🟡 In progress
**Deliverables**: Repo + 4-doc skeleton + tile-index tool + per-tile metadata dirs + scraper ethics gate drafted.

**Exit criteria**:
- `git log` shows initial commit pushed to `origin/main`
- `STATUS.md` updates live
- `tools/national_tile_index.py --dry-run` produces ~7,900 tile_count
- `tools/fetch_tile.py` exists as a stub (skeleton orchestrator) even if unimplemented

## Phase 1 — National satellite + topographic coverage (3 weeks)

**Goal**: cover the 153 priority tiles with the proven 18-layer LQV set:
DEM + Esri HD + Sentinel-2 NDVI + MapBiomas + Hansen + JRC + HydroSHEDS + OSM + GBIF + FIRMS, all 18 derived layers (cerros, streams, contours, hand, slope, aspect, hillshade, color-relief, etc.).

**Tool chains to extract from LQV**:
- `tools/build_peaks_geojson.py` (extract from LQV) — DEM-derived cerros
- `tools/build_slope_aspect.py` (extract from LQV) — slope/aspect/hillshade
- `tools/lqv_fetch_esri_hd.py` (extract from LQV) — Esri HD tile stitch
- `tools/fetch_osm.py` (new here) — OSM Overpass per tile
- `tools/fetch_sentinel2.py` (new here, derived from LQV `blender_render_*.py` deps) — STAC search + scene fetch
- `tools/fetch_mapbiomas.py` (new here)
- `tools/fetch_hansen.py` (new here)
- `tools/fetch_jrc.py` (new here)
- `tools/fetch_hydrosheds.py` (new here)
- `tools/fetch_firms.py` (new here, country-level)
- `tools/fetch_gbif.py` (new here, per-tile bbox)

**Per-tile output**:

```
data/tiles/<lon>_<lat>/
├── metadata.json         (tile_id, centroid, bbox, data_state flags)
├── dem/
│   └── cop30_clipped.tif
├── esri/
│   ├── hd_lod2_z17.png   (city-scale)
│   └── hd_lod3_z18.png   (close-zoom)
├── sentinel2/
│   ├── rgb.tif
│   ├── ndvi.tif
│   └── scl_cloudmask.tif
├── osm/
│   ├── buildings.geojson
│   ├── roads.geojson
│   ├── water.geojson
│   ├── waterways.geojson
│   ├── landuse.geojson
│   ├── places.geojson
│   ├── pois.geojson
│   └── trees.geojson
├── mapbiomas/
│   └── landcover_2023.geojson
├── hansen/
│   ├── loss.geojson
│   └── gain.geojson
├── jrc/
│   └── waterbodies.geojson
├── hydrosheds/
│   └── flow_acc.tif
├── cerros.geojson
├── streams.geojson
├── contours.geojson
├── hand.geojson
├── slope.png
├── aspect.png
├── hillshade.png
├── hillshade_multi.png     (multi-azimuth)
├── color_relief.png
└── ndvi_canopy.png
```

**Cost ceiling per tile**: ~150-300 MB raw, ~30-80 MB after compression/optimisation. 153 tiles × ~50 MB = ~7.6 GB in R2. Well within R2 free tier.

**Cron**: `paraguay-geodata-fetch-priority` (registered in `~/.hermes/cron/jobs.json` after Phase 1 milestone) runs nightly 22:00 PY. New tiles get processed one batch per night; existing tiles refresh weekly (raster sources don't change daily).

**Deploy**: `paraguay-geodata.pages.dev` (provisional; operator can override later). HTML viewer at `/?tile=<id>` and `/?tile=<id>&r=<km>`.

**Exit criteria**:
- All 153 priority tiles have a complete `data_state: true` for every layer
- Viewer loads each tile with no console errors (Cesium globe also has tile coverage map)
- A new tile (`tools/fetch_tile.py --tile-id ...`) can be built from scratch in <5 minutes

## Phase 2 — Properties + price surfaces (1 week)

**Goal**: list every property on sale from the major PY portals, cross-reference against escritura anchors, ship a hedonic $/ha raster per departamento.

**Tools** (new in this repo):
- `tools/fetch_properties.py` — multi-portal scraper (infocasas, propiedades.com.py, baiker)
- `tools/build_price_surface.py` — kriging + per-departamento output

**Data sources**:
- Listings: `infocasas.com.py`, `propiedades.com.py`, `baiker.com` (scraped, ethics-gated)
- Escritura anchors: operator-supplied `data/cadastre/escrituras/*.csv` (manual)
- Public padrones (SNC): browse-only; used as discovery surface, not parser target (per the `paraguay-open-data-fetch` skill vendor pitfalls)

**Deploy surface**:
- `/properties.html` — clustered listings + price heat overlay (toggleable on/off)
- GeoJSON: `data/properties/active_listings_<date>.geojson` (snapshot)
- Price raster: `data/prices/departamento_<id>_$/ha.tif`

**Schema**: see `docs/specs/listing-schema.json` (Phase 2 deliverable).

**Exit criteria**:
- ≥80% of currently-listed infocasas properties appear in the snapshot
- For each departamento, the price raster's leave-one-out RMSE is <X USD/ha (X set after first kriging pass)
- Clicking any listing opens a popup with: `lat/lon, price_usd, area_ha, $/ha, source, source_url, scraped_at`
- Cross-reference flag: listings where nearest escritura is <500m AND listed price is >2× median nearby

## Phase 3 — National Cesium globe + per-tile 3D planning world (1 week)

**Goal**: 3D visualisations:
- `/?cesium=1` shows the entire country at low zoom, with tile coverage heatmap
- `/?tile=<id>&cesium=1` shows the chosen tile in Cesium with Esri LOD3 imagery + 3D terrain
- `/play.html?tile=<id>` shows the low-poly Three.js planning world for the tile (LQV recipe ported)

**Tools**: extract from LQV: `build_lowpoly_world.py`, `lqv_esri_z18_lod3.py`, `lqv_hillshade_dense.py`.

**Exit criteria**:
- National Cesium globe loads in <10 seconds at default zoom
- Per-tile 3D world renders the same 18 layers as the 2D viewer in the same camera path
- Operator can navigate from global → country → tile → 3D walk in ≤3 clicks

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LQV scripts don't import cleanly in this repo | Med | High | Extract early; pin imports in `tools/_lqv_inherit.py` shim |
| R2 free tier overflowed by heavy rasters | Med | Med | Sample urban tiles at LOD3 (z=18), rural at LOD2 (z=17) only; LOD1 fallback |
| Esri z=19 returns empty tiles in rural PY (LQV-proven) | High | Low | Document it; fall back to z=18; user accepts |
| Sentinel-2 cloud-cover fails single scene retry | Med | Low | Stack 3 scenes per tile; cloud-mask via SCL band |
| Listings portals rate-limit scrapers (HTTP 429) | High | Med | Pre-flight with `ethical-web-scraping-decision` gate; budget 50 req/min per portal; cache aggressively |
| Cross-referencing listings against escrituras: too few escritura anchors | High | Low | Treat escrituras as ground truth where present; flag uncertainty in the rest |
| Operator changes their mind on the viewer pattern | Med | Low | Single `/mapa.html` with `?tile=` is the LQV-bundle "single source of truth" pattern (proven) — won't change again |

## What this plan deliberately delays

- **Blockchain**, **nft**, **tokenised land** — not asked for, not building
- **Mobile native app** — viewer works on phone, done
- **Realtime / websockets** — daily snapshots are fine
- **Per-property Cesium splats** — splats are great for a single property, not for the country
- **ML-based price prediction** — kriging gets us 80% of accuracy at 1% of the cost; revisit only if RMSE fails the Phase 2 exit criterion
