# Changelog

All notable changes to **Paraguay Geodata**.

Format: [Semantic Versioning](https://semver.org/) · Date in YYYY-MM-DD.

## [1.8.0] — 2026-07-27 — Architect export (Lucía handoff deliverable)

### Added (paid tier — Stripe-gated)
- **GeoJSON export** of the architect bundle (national + Asunción subsets), free for viewport/filtered/selection, **$29 one-time** for the full national dataset.
- **DXF export** (AutoCAD R12 ASCII, readable by AutoCAD / BricsCAD / IntelliCAD / SketchUp / QGIS), **$99 one-time**.
- **Pro yearly subscription** **$299/yr** — every format + viewport/filtered/selection auto-included.
- **Stripe checkout Worker** (`exports/checkout-worker/`):
  - POST `/checkout` creates a Stripe Checkout Session (test-mode prices pre-provisioned)
  - GET `/success` verifies payment + issues HMAC-signed 1h download token
  - GET `/download` streams from R2 or proxies from `DATASET_BASE_URL`
  - 6 unit tests pass + 10 endpoint integration tests pass
- **`/pricing` page** (`exports/web/pricing.html`) — 3 tiers, comparison table, FAQ, Stripe checkout button.
- **Data builder** `scripts/build_architect_export.py` — deterministic, versioned, schema-enveloped. Outputs:
  - `architect_export.geojson` (534 features, 3.3 MB, national)
  - `architect_export_asuncion.geojson` (49 features, 680 KB, Asunción metro)
- **Smoke tests** `tests/test_architect_export.py` (4 tests, all pass).

### Added (free — printable plan PDF)
- **`exports/web/architect-plan.html`** — printable plan page for architects who need a paper-ready artifact:
  - Captures the current map view (bbox, zoom, center) from the main site and opens with those params
  - Renders construction zones + urban zoning + flood polygons on Leaflet
  - Sidebar lists every zone in view with full ordinance metadata (height, floors, COS/FOT, retiros, allowed use, norma)
  - Includes scale bar (auto-computed for current zoom), north arrow, legend, layer toggles
  - A4 landscape print stylesheet — hides UI chrome, drops fill opacity for ink savings
- **"📐 Cómo → DWG" modal** — 4-click QGIS workflow + AutoCAD MAPIMPORT alternative for the free GeoJSON.

### Notes for architects
- **GeoJSON** opens directly in QGIS / ArcGIS / AutoCAD Map 3D.
- **DWG/DXF**: open GeoJSON in QGIS → Exportar → Guardar como → AutoCAD DWG (CRS EPSG:32721, UTM 21S), or use DXF download directly.
- **PDF plan**: open `architect-plan.html` from the main site, hit Ctrl+P / Cmd+P, choose "Guardar como PDF", orientación Horizontal, márgenes Mínimos. **Free, no Stripe.**
- **Data is preliminary**: Asunción centro has 4 zones (Ord. 246/94). National coverage requires Lucía's ordinance inputs + municipal Catastro joins.

## [1.7.0] — 2026-07-11 — Wave 7-15: environmental layers + i18n + tests

### Added
- **Service worker** (`sw.js`) with stale-while-revalidate for data, cache-first for static
- **Indigenous territories** layer (10 polygons, IWGIA + AVINA + INDI references)
- **Climate risk** layer (18 deptos, deforestation × drought combined score)
- **Flood-prone zones** layer (5 polygons, OSM + floodplain refs)
- **Data freshness badge** in sidebar with age counter (h/d/w)
- **Chart.js visualizations**: $/ha by depto (bar), property types (doughnut), top 10 deptos (bar)
- **Image gallery** in property popups (multi-image carousel + thumbnails)
- **Comparables tool** in popups (3 similar listings by type/depto/price)
- **CSV export** of all 10,898 properties (16 columns)
- **Reverse-geocode** Unknown deptos via Photon (best-effort, 50 per load)
- **Active layer count** now dynamic (was static)
- **Full Guaraní translations** (30 keys × 3 languages)
- **Auto-refresh pipeline** (`tools/auto_refresh.py`)
- **Endpoint validator** (`tools/test_endpoints.py`) — 31/31 pass
- **Browser test** (`tools/test_browser.js`) — Playwright
- **GitHub Actions CI** (`.github/workflows/ci.yml`) — 3 jobs
- **OpenAPI 3.0 spec** at `docs/api/openapi.yaml`

### Fixed
- Loading banner auto-dismisses on bootstrap complete + 8s timeout
- `loadBarrios()` no longer fetches 3 missing files
- Duplicate `sidebarToggle` button removed
- Duplicate `main` CSS rule on mobile consolidated
- `updateStats()` now dynamic
- Old text-based `$/ha` chart replaced with Chart.js

### Removed (25.7 MB freed)
- `properties_tulugar.geojson` (24.2 MB) — never referenced
- `natural.geojson` (268 KB)
- `properties_meta.json` (empty)
- `admin/{barrios_int,barrios_sub,distritos_sub,localidades,deptos}.geojson`

## [1.6.0] — 2026-07-11 — Wave 6: image gallery + honest docs

### Added
- Image gallery in property popups
- Comparables tool
- Honest STATUS.md (no more marketing claims)

## [1.5.0] — 2026-07-11 — Wave 5: mobile redesign + filters + cleanup

### Added
- Mobile drawer sidebar (hidden by default, hamburger menu)
- Real filters: price/type/beds/area + apply-to-map
- CSV export button
- 8s loading banner timeout fallback

### Fixed
- Active layer count dynamic
- Mobile CSS duplicate rules consolidated

## [1.4.0] — 2026-07-11 — Wave 4: fair-price ML

### Added
- Fair-price ML model (10,840 samples, 14 per-depto regressions)
- Yield calculator (gross/net yield, payback years)
- Fair-price badges on property popups

### Known limitations
- Fair-price R² ≈ 0.017 (decorative, not actionable)

## [1.3.0] — 2026-07-11 — Wave 3: market signals + share

### Added
- Market signals (auto-computed)
- Share view, embed widget, geolocation buttons
- URL hash sync (?lat=&lon=&z=&layers=)
- PWA manifest

## [1.2.0] — 2026-07-11 — Wave 2: PII scrub + Catastro + geocoder

### Added
- PII scrubbing (10,898 listings)
- Catastro Nacional WFS integration (4 layers)
- Photon geocoder
- Marker clustering
- i18n (es/en/gn)
- WCAG 2.2 AA accessibility

## [1.1.0] — 2026-07-11 — Wave 1: bug fixes

### Fixed
- Duplicate `LAYER_GROUPS` const
- `loadINBIOSoja()` orphan call
- `gbif_species` reference
- `updateLayerCount` guard for non-layer IDs
- `buildGroup` targetLayer fix

## [1.0.0] — 2026-07-11 — Initial release

- 10,898 priced real-estate listings
- 14,835 OSM roads
- 50,000 OSM building footprints
- 200 GBIF species
- BCP macro snapshot
- NASA POWER climate
- INBIO crop area
- 21 toggleable layers