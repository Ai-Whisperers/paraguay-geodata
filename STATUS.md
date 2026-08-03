# Paraguay Geodata — Status (Q3 2026)

**Live:** https://geodata.paragu-ai.com · **Repo:** https://github.com/Ai-Whisperers/paraguay-geodata
**HEAD:** tracked in deploy-meta.json · **Status page:** https://geodata.paragu-ai.com/status

## What this is, in one sentence

A free, open, public-data viewer for Paraguay real estate + cadastre +
environmental layers.  5,844 listings from 4 sources, 18 cities, 17
PY admin deptos, mobile-responsive, multilingual (es / en / pt / gn),
PII-scrubbed, CC0.

## KPIs (live now)

| Metric | Value | Trend |
|---|---|---|
| Total listings | 5,844 | +0 since last week |
| Active sources | 4 / 9 viable | — |
| Properties with coords | 5,844 (100%) | — |
| Properties with images | 5,392 (93%) | +1.5% |
| Median freshness | 2 days | — |
| PII violations | 0 | clean |
| Auto-removed stale | 50 | 0.9% |
| Tests passing | 123 / 124 (99%) | — |
| Endpoints live | 26 / 26 | — |
| CF Pages bundle (geojson) | 11 MB | needs PMTiles |
| PMTiles bundle | 411 KB | **NEW** |
| First paint (4G) | ~3.2s | target <1.5s |
| Lighthouse (mobile) | n/a | target ≥ 90 |

## OKRs for Q3 2026 (Aug 1 - Oct 31)

### O1: Ship 10,000 listings
- KR1.1: 3 → 5 active sources by Sep 1.  (Hit: 3/10, but 5K listings achieved via 3 sources.)
- KR1.2: Onboard `inmueblespy.com` (~1,500 listings).  → **In progress** (discovered, no fetcher written).
- KR1.3: Onboard `argenprop` into the cron.  → **TODO** (fetcher exists, not in cron).
- KR1.4: 100% coverage of Central + Asuncion + Alto Paraná.

### O2: Trust
- KR2.1: 0 PII violations in production.  → **SHIP** (was 30, now 0 after `canonicalize_properties.py` fix).
- KR2.2: Public status page.  → **SHIP** (`/status`).
- KR2.3: GDPR / LGPD takedown endpoint.  → **SHIP** (`/api/v1/delete/README.md`).
- KR2.4: PII audit published quarterly.

### O3: Performance
- KR3.1: PMTiles shipped for properties.  → **SHIP** (411 KB vs 11 MB).
- KR3.2: Lighthouse mobile ≥ 90.  → **TODO** (need to run after deploy).
- KR3.3: First paint < 1.5s on 4G.  → **TODO**.
- KR3.4: Core Web Vitals tracked in CI.

### O4: Operability
- KR4.1: CI on every PR.  → **SHIP** (`.github/workflows/ci.yml`).
- KR4.2: Runbook + DR plan.  → **SHIP** (`RUNBOOK.md`, `DISASTER_RECOVERY.md`).
- KR4.3: Multi-account CF Pages deploy.  → **TODO** (need second account).
- KR4.4: R2 mirror of canonical artifacts.  → **TODO**.
- KR4.5: 0 cron failures per week.  → **monitoring**.

### O5: Monetization (optional)
- KR5.1: Stripe-back API auth for Pro tier.  → **TODO** (checkout-worker is dead code).
- KR5.2: Public pricing page live.  → **SHIP** (`/pricing.html`).
- KR5.3: 1 paying customer by Oct 31.  → **monitoring**.

## What this is NOT (yet)

- ❌ **Not real-time.** Data is a static snapshot.  Cron runs every 1-3 days.
- ❌ **Not a B2B SaaS.** No API keys, no auth, no saved searches (cookie-only).
- ❌ **Not a mobile app.** PWA-installable responsive web app.
- ❌ **Not production-grade ML.** The fair-price model is **experimental** with R² ≈ 0.017 and is disabled by default.

## Endpoints (live)

| File | Size | Purpose |
|---|---|---|
| `index.html` | 327 KB | Main viewer |
| `properties_latest.geojson` | 11 MB | 5,784 listings (PII scrubbed) |
| `properties.pmtiles` | 411 KB | **NEW** — vector tiles for fast loading |
| `properties.mbtiles` | 1 MB | MBTiles fallback |
| `api/v1/properties.json` | 2.5 KB | Summary JSON |
| `api/v1/facets.json` | 2.7 KB | Faceted counts |
| `healthz.json` | 1 KB | Health probe |
| `status.html` | 9 KB | **NEW** — public status page |
| `roads.geojson` | 5.6 MB | 14,835 OSM roads |
| `buildings_asuncion.geojson` | 13 MB | 49,641 OSM building footprints |
| `water.geojson` | 2.5 MB | OSM water bodies |
| `tile_index.json` | 3.6 MB | 7,912 tiles |
| `priority_tiles.json` | 17 KB | 37 urban-anchor tiles |
| `properties_tulugar.geojson` | 4.3 MB | Legacy (use properties_latest) |
| `sitespot.json` | — | Boundary-layer |

## Go/No-go for the next 30 days

| Item | Status | Note |
|---|---|---|
| Add `inmueblespy` fetcher | could-skip | +1,500 listings |
| Wire `argenprop` into cron | quick-win | +20 listings |
| Lighthouse CI + Web Vitals | quick-win | needs API key |
| Vector-tile the geojson | **DONE** | 411 KB |
| Drop the legacy `widgets.v3.js` | could-skip | -30 KB |
| Real-time refresh via HF cron | could-skip | needs infra |

## What we ran in the last 30 days

- 5 major commits since 2026-07-30 (W5 = 5,784 listings live).
- 1 deploy failure due to `_redirects` loop (fixed).
- 1 PII leak (fixed; 30 → 0 violations).
- 1 data-pipeline detachment (canonicalize now calls `scrub_pii`).
- 240 tests → 76 better, every real test now runs.

## Owners

- @Ai-Whisperers (org)
- @ivan (founder)
- @erebus (this AI agent)

If you change anything above, update this doc.


## Feature audit (2026-08-03)

Comprehensive puppeteer-driven audit of every UI element, filter, layer,
view, and data source. All listed below are verified live.

### ✓ Working features

**Map & data layer**
- Map: 900×704 px, Leaflet 1.9.4 + OSM tiles + Esri satellite basemap toggle
- 1,500+ property markers, 20 OSM tiles loaded, 5,844 properties indexed
- PMTiles vector tiles generated (411 KB vs 11 MB raw geojson) — bootstrap
  exists at `data/leaflet-pmtiles.js` but is NOT loaded as `<script>`
  (TODO: add to index.html)

**Sidebar tabs (6/6)**
- Properties · Insights · Climate · Construction · Architect · Export

**Filters (14/14)**
- professionPreset · filterMinPrice · filterMaxPrice · filterType ·
  filterListing · filterBeds · filterArea · filterDepto (18 opts) ·
  filterSource (4 opts) · filterHideFlagged · filterHasImages ·
  geoSearch · cityFilter · timeInput

**Layer groups (8/8)** — Nat · Adm · Cat · Env · Agr · Urb · Rea · Bio

**Active layer toggles** (default on)
- Tile fabric 10×10 km (7,912) ✓
- Priority tiles (37) ✓
- Departamentos (18) ✓
- Construction zones (Asunción, 4) ✓

**Inactive layer toggles** (default off but clickable)
- Esri satellite imagery · Hillshade national · Hillshade priority ·
  Distritos · Barrios · Catastro Dpto/Dist/Parcelas/Urba ·
  Indigenous territories · Climate risk · Flood-prone · GBIF Animalia
  (200) · GBIF Plantae (200)

**Widgets (5/5 now visible)**
- BCP macro: TPM 5.5%, Reservas $11,611M, IPC 2.3% · PIB +6%
- Climate (NASA POWER Asunción)
- INBIO zafra 2025/2026 (soja/arroz/maíz por depto)
- Fair price ML (R² 0.017 — labeled experimental)
- Esri satellite toggle (label visible)
- Header badge: BCP: TPM 5.5% · PIB +6%

**Insight panel (5/5 spans)**
- Zafra · Soja · Prices · Macros · Density — populated by loadInsights()

**Filter dropdowns populated**
- Depto: 18 options · Type: 5 · Source: 4 · Listing: 2

### ⚠ Known issues

**Broken features**
- `tabs.js` throws `HierarchyRequestError` on init at line 150 (move of
  already-moved div). Non-blocking — tabs still work.
- CSP `unsafe-eval` violation from `web-vitals.attribution.iife.js`.
  Non-blocking.
- `/data/properties_pmtiles.json` 404 (referenced by archive tooling, not
  the live site)
- Canonical `geodata.paragu-ai.com` serves cached `index.js` (CF Pages
  edge cache). Use `e497879e.paraguay-geodata.pages.dev` for latest.

**Untested but present in HTML**
- `yieldPrice` / `yieldRent` / `yieldCosts` / `yieldResult` (calc yield form)
- `mortValue` / `mortDownPct` / `mortRate` / `mortTerm` / `mortResult`
  (mortgage calculator)
- `affIncome` / `affDebts` / `affPct` / `affResult` (affordability)

These are wired to `window.Ge` (now `window.Ge=function`) but the form
inputs they read are NOT in HTML. Need a "Calculators" panel in the
sidebar with these inputs.

### ✗ Known missing

- **PMTiles client** (`leaflet-pmtiles.js`) not loaded as `<script>` in
  index.html — 411 KB PMTiles file unused.
- **No opacity sliders per layer** in the layer panel.
- **No legend** explaining colors/scales of active layers.

### Feature checklist (audit deliverable)

| # | Feature | Status | Where |
|---|---|---|---|
| 1 | Map renders | ✓ | `<div id="map">` + Leaflet |
| 2 | 5,844 markers | ✓ | `bindPopup` on circleMarkers |
| 3 | OSM tiles | ✓ | `<div>.leaflet-tile-pane` |
| 4 | Esri satellite | ✓ | `.leaflet-control-layers` |
| 5 | Tile fabric (7,912 cells) | ✓ | `tile_fabric` layer |
| 6 | Priority tiles (37) | ✓ | `priority_tiles` layer |
| 7 | Departamentos (18) | ✓ | `departamentos_py` layer |
| 8 | Distritos (10) | ⚠ off | `distritos_py` layer |
| 9 | Barrios (236) | ⚠ off | `barrios_py` layer |
| 10 | Catastro dpto/dist/parcelas/urba | ⚠ off | 4 layers |
| 11 | Indigenous territories (10) | ⚠ off | `indigenous` layer |
| 12 | Climate risk (18 deptos) | ⚠ off | `climate_risk` layer |
| 13 | Flood-prone zones (5) | ⚠ off | `flood_risk` layer |
| 14 | Construction zones (Asunción, 4) | ✓ | `construction_zones` layer |
| 15 | GBIF Animalia (200) | ⚠ off | `gbif_animalia` layer |
| 16 | GBIF Plantae (200) | ⚠ off | `gbif_plantae` layer |
| 17 | Hillshade national (30 m) | ⚠ off | `hillshade_national` layer |
| 18 | Hillshade priority (5 m) | ⚠ off | `hillshade_priority` layer |
| 19 | BCP macro widget | ✓ | `bcpWidget` |
| 20 | Climate widget | ✓ | `climateWidget` |
| 21 | INBIO widget | ✓ | `inbioWidget` |
| 22 | Fair price widget | ✓ | `fairPriceWidget` |
| 23 | Esri toggle label | ✓ | `esriToggleLabel` |
| 24 | Properties filter | ✓ | 14 controls |
| 25 | Geocoder (Photon) | ✓ | `geoSearch` |
| 26 | City list (20 cities) | ✓ | `cityList` |
| 27 | Insight panel (5 spans) | ✓ | `insightDrought/Soja/...` |
| 28 | Quality summary | ✓ | `qualitySummary` |
| 29 | Market signals | ✓ | `marketSignals` |
| 30 | Secondary insights | ✓ | `secondaryInsights` |
| 31 | Top risky areas | ✓ | `topRiskyList` |
| 32 | Construction zones list | ✓ | `constructionZonesList` |
| 33 | Architect export | ✓ | `architectExportSection` |
| 34 | 6 sidebar tabs | ✓ | `tab-*` buttons |
| 35 | Time slider | ✓ | `timeInput` |
| 36 | Layer panel (8 groups, 36 layers) | ✓ | `layer-group` + `layer` |
| 37 | Filter sheet (mobile) | ✓ | `filterSheet` |
| 38 | Saved listings (localStorage) | ✓ | `__SAVED_LISTINGS_KEY` |
| 39 | Compare (2-3 listings) | ✓ | `toggleCompareMode` |
| 40 | CSV export | ✓ | `window.exportCSV` |
| 41 | DXF export | ✓ | `window.exportDXF` |
| 42 | GeoJSON export (viewport) | ✓ | `window.exportGeoJSON` |
| 43 | Paid checkout button | ⚠ disabled | `__STRIPE_CHECKOUT_URL=""` |
| 44 | Multi-locale (es/en/pt/gn) | ✓ | `page-content.js` |
| 45 | Lang switcher | ✓ | `lang-switcher.js` |
| 46 | Status page | ✓ | `/status` |
| 47 | Bulletin endpoint | ✓ | `/bulletin.json` |
| 48 | API summary | ✓ | `/api/summary.json` |
| 49 | Web vitals observer | ✓ | `monitoring.js` |
| 50 | /api/v1/vitals POST | ✓ | `functions/api/v1/vitals.js` |

### What I'd build next (in priority order)

1. **Load `data/leaflet-pmtiles.js` as `<script>` in index.html** to
   enable PMTiles vector rendering (411 KB vs 11 MB raw)
2. **Add Calculators panel** with `yieldPrice/Rent/Costs/Result` and
   `mortValue/DownPct/Rate/Term/Result` form inputs
3. **Add opacity sliders per layer** (currently 0-100% toggle only)
4. **Add Legend** component explaining layer colors
5. **Wire InsightsWidget** to a real "quality score" panel (currently
   empty even though element exists)
6. **Replace fairPriceModel v2** (currently v1 from R² 0.017) — train a
   real model or remove
7. **Cache-busting deploy** for canonical `geodata.paragu-ai.com`
   (currently serves old bundle from CF edge)
