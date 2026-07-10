# Architecture — Paraguay Geodata

## North-Star Design Principles

1. **Single source of truth for parameterised viewers.** One `/mapa.html` with `?tile=<lon>_<lat>&r=<km>` and a UI picker, NOT N files for N tiles. (Lqv-bundle pattern, 2026-07-06 lesson.)
2. **Tiles are units of reproducibility.** Every 10×10 km box is independently re-buildable from `tools/fetch_tile.py`. No "magic" cross-tile state.
3. **Listings + deeds = hedonic truth.** Both are needed. Listings are noisy (re-listed listings, "as price negotiable", speculative); escrituras are clean (transaction price, exact area, real coords). Cross-reference both.
4. **Heavy rasters go to R2, never to Pages.** Cloudflare Pages has a 25 MiB per-file cap. Sentinel-2 clips, Esri HD, Hansen rasters, DEMs — all R2-backed via `/r2/<key>` URLs. Pages only ships small GeoJSONs and the HTML.
5. **Operator is the boss.** Every scraper, every API call, every costly tile fetch — wrote it down first in `docs/operations/`. No silent decisions.

## Top-Level Layout

```
paraguay-geodata/
├── README.md              ← entry point
├── ARCHITECTURE.md        ← THIS FILE
├── CLAUDE.md              ← instructions for AI agents running this repo
├── STATUS.md              ← live state of every phase + every track
├── PROVENANCE.md          ← source data licensing + attribution
├── CREDITS.md             ← humans + tools + upstream providers
├── LICENSE                ← MIT
├── tools/                 ← all data fetching + analysis scripts
├── templates/             ← re-usable starter scripts
├── tests/                 ← pytest + per-tile smoke tests
├── scripts/               ← shell drivers (cron-friendly)
├── docs/
│   ├── INDEX.md           ← map of every doc
│   ├── sources/           ← per-source data catalogue
│   │   ├── satellite.md
│   │   ├── cadastre.md
│   │   ├── listings.md
│   │   ├── prices.md
│   │   └── biodiversity.md
│   ├── operations/        ← procedural playbooks (operator-facing)
│   │   ├── national-tile-fabric.md
│   │   ├── properties-pipeline.md
│   │   ├── price-model.md
│   │   └── api-key-checklist.md
│   ├── ethics/            ← decision trees + policies
│   │   └── scraper-policy.md
│   ├── specs/             ← schemas: GeoJSON property schema, etc.
│   └── reference/         ← upstream API docs in markdown
├── data/                  ← data lakes (gitignored / R2-backed)
│   ├── tiles/             ← tiles/<lon>_<lat>/  (DEM, Esri, S2, OSM, etc.)
│   ├── properties/        ← listings snapshots
│   ├── prices/            ← per-departamento $/ha raster
│   └── cadastre/          ← escritura anchors + public padron indexes
├── exports/
│   ├── web/               ← CF Pages deploy mirror (small GeoJSONs + HTML)
│   │   ├── index.html
│   │   ├── mapa.html
│   │   ├── properties.html
│   │   ├── cesium3d.html
│   │   ├── data/          ← small GeoJSONs + tile index
│   │   └── shared/        ← JS, CSS, fonts (small)
│   └── big_data_excluded_from_deploy/   ← R2-bound rasters (source of truth)
├── splats/                ← state machine + per-phase notes
│   ├── TODO.md
│   └── PHASES.md
└── assets/                ← logos, screenshots, design refs
```

## Pipeline Architecture

```
SOURCE          →  FETCH            →  PROCESS            →  PUBLISH
─────────────────────────────────────────────────────────────────────
Copernicus GLO-30 → tools/fetch_tile.py → tools/build_slope_aspect.py
Sentinel-2 L2A    → tools/fetch_tile.py → NDVI, cloud mask
Esri World        → tools/lqv_fetch_esri_hd.py → stitched PNG + LOD3
OSM Overpass      → tools/fetch_osm.py     → roads/water/buildings
MapBiomas PY      → tools/fetch_mapbiomas.py → class polygons
Hansen GFC        → tools/fetch_hansen.py  → loss/gain polygons
JRC GSW           → tools/fetch_jrc.py     → waterbodies polygons
HydroSHEDS        → tools/fetch_hydrosheds → flow accumulation
FIRMS             → tools/fetch_firms.py   → fire hotspots CSV
GBIF              → tools/fetch_gbif.py    → species observations

infocasas         → tools/fetch_properties.py → listings GeoJSON
propiedades.com.py → tools/fetch_properties.py → listings GeoJSON
baiker.com.py     → tools/fetch_properties.py → listings GeoJSON
escrituras        → manual anchor tables    → deed anchors GeoJSON

listings + escrituras → tools/build_price_surface.py → $/ha raster (per depto)
                                              → listing points + price-heat overlay

ALL of the above  → exports/web/mapa.html      → single source of truth viewer
              → exports/web/properties.html   → listings + price overlay
              → exports/web/cesium3d.html     → 3D national globe (optional)
```

## Key Technical Decisions

### Tile fabric: 10×10 km, EPSG:4326

Why 10×10 km:
- Matches LQV's proven scale (the viewer was built and stress-tested at exactly this size)
- Copernicus GLO-30 tiles (~1°×1°) neatly dissect into ~100×100 cells at this size
- Esri z=17 imagery yields ~1 m/pixel → 1 MB per PNG after Pillow optimise — well within R2 free tier
- One tile = one asset bundle that can be re-fetched independently on demand

Total tiles: ~1,000 covering Paraguay's 406,752 km². ~120 tiles in urban/priority areas by Phase 1.

### Storage tier split

| Tier | Backend | Cdn | Use |
|---|---|---|---|
| HTML + JS + small GeoJSONs (≤25 MiB/file) | CF Pages | global | `/exports/web/**` |
| Heavy rasters (DEM, Esri HD, S2, Hansen) | CF R2 | public via custom domain | `/exports/big_data_excluded_from_deploy/**` + `/exports/web/data/tiles/<tile>/`** |
| Listings / prices / state | JSON + GeoJSON | (low volume, ships via Pages) | `/exports/web/data/**` |

The `wrangler.jsonc` (CF config) wires R2 bucket `paraguay-geodata-raster` to a public custom domain `r2.paraguay-geodata.com` (TBD).

### Single-source-of-truth viewer

`/mapa.html?tile=21JWL_2&r=10` — one file, all tiles. The file fetches a `tile-index.json` (under 100 KB) that describes the bbox + parcel centroid + which data files exist for that tile, then lazy-loads each layer's GeoJSON from the correct URL.

**Trade-off accepted**: viewer fan-out is N HTTP requests per page load (one per layer). For tiles with all 18 layers, that's ~25 fetches in parallel, all small JSONs. R2 + Pages handle this trivially.

### Listings + deeds

- Listings: scraped from public portals. Ethics gate per `docs/ethics/scraper-policy.md`. Dedup by `(source, source_id)` — every listing gets a stable hash.
- Deeds (escrituras): manually-anchored, treat as truth. Push every scraped listing against the nearest escritura points; flag where listings disagree with deeds (price out of band, area mismatch, wrong district).
- Output schema: see `docs/specs/listing-schema.json` (Phase 2).

### Hedonic price raster

Phase 2 details in `docs/operations/price-model.md`. Quick summary:
- Per listing point: `(lon, lat, district_code, $/ha, attrs)` where attrs = `{bedrooms, has_water, has_power, has_road_access, escritura_anchor_distance_m}`
- Per departamento: kriging via `pykrige` (Ordinary Kriging with exponential variogram)
- Cross-validation: leave-one-out RMSE per departamento, fail if RMSE > $X
- Output: GeoTIFF per departamento + a single national GeoTIFF as fallback
- Sampled to 30 m/px to match DEM resolution

## Cross-References

- **Lqv-bundle skill** (the technique):
  `~/.hermes/skills/lqv-bundle/SKILL.md` — owns the umbrella
- **Satellite-to-blender-pipeline skill** (the class):
  `~/.hermes/skills/devops/satellite-to-blender-pipeline/SKILL.md`
- **Paraguay-open-data-fetch skill** (the source catalogue):
  `~/.hermes/skills/paraguay-open-data-fetch/SKILL.md`
- **Ethical-web-scraping-decision skill** (the gate):
  `~/.hermes/skills/ethical-web-scraping-decision/`

## What this architecture deliberately does NOT include

- **Blockchain / on-chain anything.** No need.
- **Custom engine (Cesium for Unreal, UE5).** LQV Path 1 is an option for photoreal; not for national default. Cesium JS + R2 tiler is the rule. Web stack only.
- **Authentication / user accounts.** Public read-only data. Listings scraping is read-only too.
- **Mobile native app.** The HTML viewer works on phone. Done.
- **Realtime.** All raster + listings snapshots are daily/weekly. No WebSocket.
