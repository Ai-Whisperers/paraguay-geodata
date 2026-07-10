# TODO — Paraguay Geodata

Phase-by-phase task list. Update before each commit.

## Phase 0 — Skeleton (in progress)

- [x] Create repo + 4-doc skeleton (README / ARCHITECTURE / CLAUDE / STATUS)
- [x] Add .gitignore, LICENSE, CREDITS, pyproject, docs/INDEX
- [x] tools/national_tile_index.py — 7,912-tile fabric working
- [x] tools/fetch_tile.py — stub orchestrator
- [x] tools/build_peaks_geojson.py — stub (LQV algorithm recipe ref'd)
- [x] tools/build_slope_aspect.py — stub (LQV algorithm recipe ref'd)
- [x] tools/fetch_properties.py — stub (ethics gate drafted)
- [x] tools/build_price_surface.py — stub
- [x] docs/operations/national-tile-fabric.md
- [x] docs/operations/properties-pipeline.md
- [x] docs/operations/price-model.md
- [x] docs/ethics/scraper-policy.md
- [ ] First commit + push (about to do)
- [ ] Update STATUS.md with first-commit timestamp

## Phase 1 — National satellite + topographic coverage (queued)

- [ ] Provision CF R2 bucket `paraguay-geodata-raster`
- [ ] Provision CF Pages project `paraguay-geodata` (custom domain TBD)
- [ ] Implement `tools/fetch_esri_hd.py` (port from LQV `lqv_fetch_esri_hd.py`)
- [ ] Implement `tools/fetch_dem.py` (Copernicus GLO-30)
- [ ] Implement `tools/fetch_sentinel2.py`
- [ ] Implement `tools/fetch_osm.py`
- [ ] Implement `tools/fetch_mapbiomas.py`
- [ ] Implement `tools/fetch_hansen.py`
- [ ] Implement `tools/fetch_jrc.py`
- [ ] Implement `tools/fetch_hydrosheds.py`
- [ ] Implement `tools/fetch_firms.py`
- [ ] Implement `tools/fetch_gbif.py`
- [ ] Fill `tools/build_peaks_geojson.py` (algorithm)
- [ ] Fill `tools/build_slope_aspect.py` (algorithm)
- [ ] Wire `tools/fetch_tile.py` to chain all 26 layers per priority tile
- [ ] Cron: `paraguay-geodata-fetch-priority` (nightly 22:00 PY)
- [ ] Cron: `paraguay-geodata-pages-redeploy` (every 6h)
- [ ] Build `exports/web/index.html` (national landing)
- [ ] Build `exports/web/mapa.html` (per-tile Leaflet, parameterised)
- [ ] Defer to Phase 3: `exports/web/cesium3d.html`, `exports/web/play.html`
- [ ] All 153 priority tiles green for data_state
- [ ] Phase 1 commit tagged `phase1`

## Phase 2 — Properties + price surfaces (queued)

- [ ] Implement `tools/fetch_properties.py` (3 portals)
- [ ] Implement `scripts/dedupe_listings.py`
- [ ] Implement `scripts/match_escrituras.py`
- [ ] Implement `tools/build_price_surface.py` (pykrige per dept + national blend)
- [ ] `docs/specs/listing-schema.json`
- [ ] `docs/specs/price-surface-schema.json`
- [ ] `exports/web/properties.html` (listings + price overlay)
- [ ] Cron: `paraguay-geodata-fetch-properties` (Sun 03:00 PY)
- [ ] Cron: `paraguay-geodata-build-price-surface` (Sun 05:00 PY)
- [ ] Cron: `paraguay-geodata-rebuild-properties-deploy` (Sun 06:00 PY)
- [ ] Phase 2 commit tagged `phase2`

## Phase 3 — National Cesium globe + per-tile 3D planning world (queued)

- [ ] Port LQV `tools/build_lowpoly_world.py` (Three.js low-poly viewer)
- [ ] Extract LQV `tools/lqv_esri_z18_lod3.py`
- [ ] Extract LQV `tools/lqv_hillshade_dense.py`
- [ ] `exports/web/cesium3d.html` — national globe
- [ ] `exports/web/play.html` — per-tile Three.js planner
- [ ] Phase 3 commit tagged `phase3`

## Decision points to revisit

- Custom domain name (currently undefined)
- Whether the price raster needs a paid API (most viewing is via static GeoJSON — probably not in Phase 3)
- Whether to add a 4th listings portal (encuentrobienes / adinco) — Phase 2.1 backlog
