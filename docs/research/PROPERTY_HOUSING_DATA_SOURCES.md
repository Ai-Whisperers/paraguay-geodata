# Property + Housing Data Sources Survey — Paraguay
**Date:** 2026-07-11
**Author:** Erebus (automated survey + manual probes)
**Goal:** Catalog every open + publicly-accessible source of housing/property/land data for Paraguay, with a verified fetch verdict so we can prioritize integrations.

---

## TL;DR — The Big Wins

| Source | What you get | Records | Fetch difficulty | Verdict |
|---|---|---|---|---|
| **Catastro Nacional WFS** | Official parcel polygons with `valor_tierra`, `valor_edificado`, `superficie`, `padron`, `nro_matricula` | **2,191,342 active parcels** | ✅ Open WFS 2.0 (no auth, EPSG:32721) | **SHIP FIRST** |
| **TuLugar.com `/api/listings`** | Real-estate listings with full schema (price, currency, beds, area, lat/lon, source platform, agent whatsapp) | 15,000+ (paginated 100/page) | ✅ Public API, no auth, paginate offset 0–11000+ | **SHIP SECOND** |
| **BCP IEF PDF** | Quarterly banking-stability report including mortgage loan portfolio by bank, delinquency rates | 1.3 MB per report | ✅ Direct PDF, just download | **SHIP THIRD** |
| **Properstar** | Aggregated global listings for PY (3,524 listings across 18 deptos with coords) | 3,524 | ⚠️ HTML scraping needed (sitemap 403/429) | Nice to have |
| **Catastro PDF "Precios Rurales"** | Per-district land prices by soil class — official government valuation table | Multi-page table | ✅ PDF | **SHIP WITH WFS** |
| **Geofabrik roads.shp** | National road network (already in our Geofabrik dump) | ~50K segments | ✅ Extract from existing shp.zip | **SHIP FOURTH** |
| **INBIO parcela×crops** | Land-use overlay on top of cadastre | 17 deptos | ✅ Already parsed | **SHIP WITH WFS** |

---

## 1. 🏛 CADASTRAL & LAND REGISTRY (the gold layer)

### 1.1 Servicio Nacional de Catastro — **GOLD STANDARD**
- **URL:** `https://www.catastro.gov.py/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities`
- **Status:** ✅ Public WFS 2.0, no auth, returns JSON / GML / SHAPE-ZIP / CSV
- **Layers (verified by probe):**

| Layer | Description | Records | Bounding box |
|---|---|---|---|
| `snc:parcelas_activas` | Active cadastral parcels (THE MONEY LAYER) | **2,191,342** | Whole PY (EPSG:32721 UTM 21S) |
| `consulta:ly_parc_view` | Public parcels view | ~? (auth-gated, returns 401) | Same |
| `snc:ly_dpto` | Departamentos (18) | 18 | Whole PY |
| `snc:ly_dist` | Distritos (268!) | 268 | Whole PY |
| `snc:ly_urba` | Urban zones | 470 | Eastern PY (no Chaco) |
| `snc:area_afectada` | Affected areas | ? | Whole PY |

- **Parcel schema (snc:parcelas_activas — 28 columns):**
  - `id`, `objectid`, `id_parcela`
  - `dpto` (letter A-P+ASU), `dist`, `padron` (cadastral number)
  - `zona`, `mz` (manzana), `lote`, `finca`
  - **`nro_matricula`** (registry number)
  - **`ccatastral`** (full catastral code: `J09000005357`)
  - `obs` (notes)
  - `mz_agr`, `lote_agr` (rural subdivision)
  - `tipo_pavim`, `tipo_cuenta`
  - **`hectareas`** (size in hectares)
  - **`superficie_tierra`** (land area m²)
  - **`superficie_edificado`** (built area m²)
  - **`valor_tierra`** ← **OFFICIAL LAND VALUATION PER PARCEL**
  - **`valor_edificado`** ← **OFFICIAL BUILDING VALUATION**
  - `tipo`, `referencia`, `clave_comparacion`
- **CRS:** EPSG:32721 (UTM 21S) — must reproject to 4326 for web display
- **Rate limit:** Unknown — should add 0.5s between requests, fetch in bbox tiles
- **Sample queries:**
  ```bash
  # First 5 parcelas in JSON
  curl 'https://www.catastro.gov.py/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=snc:parcelas_activas&count=5&outputFormat=application/json'
  
  # Hit count only
  curl 'https://www.catastro.gov.py/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=snc:parcelas_activas&resultType=hits&outputFormat=application/json'
  
  # Bbox filter (Asunción)
  curl '...&typeName=snc:parcelas_activas&bbox=-57.65,-25.35,-57.50,-25.20,urn:ogc:def:crs:EPSG::4326&count=100'
  ```
- **WMS also available:** `https://www.catastro.gov.py/geoserver/wms?service=WMS&version=1.1.1&request=GetCapabilities` (same layers, raster tiles, perfect for direct Leaflet overlay)
- **Verification:** Tested with `?count=1` returning 1 feature with all 28 fields populated, hit count `numberMatched="2191342"` confirmed.

### 1.2 Catastro PDFs (valuation references)
- **URLs:** https://www.catastro.gov.py/public/
  - `a67509_2016.10 - SISTEMA DE VALORACION. PRIMERAS APROXIMACIONES.pdf` — system for valuation
  - `dab07e_Precios_Rurales_Rubén_Maidana.pdf` — **PER-DISTRICT RURAL LAND PRICES**
  - `c3a7a2_Valoración_Inmobiliaria_en_el_Paraguay.pdf` — urban/suburban/mixed/rural zoning
- **Verdict:** ✅ PDFs are linked from public page. Each district has a $/ha reference price per soil class. **Direct download, no auth.** Already shows ~600-15,000 USD/ha in published references.

### 1.3 Dirección General de los Registros Públicos (DGRP)
- **URL:** https://dgrp.gov.py/
- **What they have:** Final ownership records (who owns the land). Less geographic, more legal.
- **Status:** ⚠️ Front page loads, no public bulk API. The DGRP is part of Poder Judicial. May need individual lookup per matricula number.
- **Verdict:** Skip for now — what we already have (parcela polygons + matricula) lets users query DGRP individually if they want ownership details.

### 1.4 INDERT (Instituto Nacional de Desarrollo Rural y de la Tierra)
- **URL:** https://www.indert.gov.py/indert/index.php/
- **What they have:** Asentamientos (rural settlements), agrarian reform, formalization of landless farmers
- **Status:** ✅ Site loads. Public PDF maps + lots of agrarian history.
- **Verdict:** Worth fetching their asentamientos polygons if available. **Currently no public WFS.** Could scrape PDFs for asentamiento lists.

---

## 2. 📡 OPEN DATA PORTALS (datos.gov.py)

The site `datos.gov.py` does not have a property/housing category. The OGP commitment (PY0017) noted "El Paraguay no cuenta actualmente con un portal web público que provea datos abiertos de diferentes instituciones públicas." Verified — there's no central dataset.

What does exist:
- **DNCP** (https://contrataciones.gov.py/datos/) — public procurement data. Could include construction tenders, but no housing-specific dataset.
- **MEF open data portal** — fiscal data, not property.

**Verdict:** datos.gov.py is a dead-end for property data. Skip.

---

## 3. 🏢 REAL-ESTATE PORTALS — comparable to infocasas

### 3.1 TuLugar.com — **TOP TIER**
- **Public API:** `https://tulugar.com/api/listings?limit=100&offset=N`
- **Auth:** None required
- **Pagination:** Limit capped at 100 per page (verified `?limit=500&offset=0` returns 100). Pagination works through at least offset=11500.
- **Total estimated:** 15,000-16,000 listings (matches their "15,261 properties" marketing copy)
- **Schema per listing (verified, 100+ fields):**
  - `id` (UUID), `slug`, `source_url`, `source_platform` ← **the original portal it came from**
  - `title`, `description` (HTML, supports ES/EN/PT translations)
  - `price`, `currency` ("PYG" or "USD")
  - **`price_usd`** (auto-converted by TuLugar!)
  - `listing_type` ("rent"/"sale"), `property_type` ("house"/"apartment"/"land"/"commercial")
  - `bedrooms`, `bathrooms`, `area_sqm`, `lot_size_sqm`, `covered_area_sqm`, `parking_spaces`
  - `address`, `city`, `neighborhood`, `state_province`, `country`
  - **`latitude`, `longitude`** (most listings have these!)
  - `images[]`, `video_url`, `tour_3d_url`
  - `source_platform` (e.g. `"century21.com.py"`, `"infocasas.com.py"`)
  - `source_agent_name`, `source_agent_whatsapp`
  - `verified`, `favorites_count`, `leads_count`
  - `features[]`, `land_services[]`, `commercial_*` fields for commercial properties
  - `currency` conversion metadata
- **Special insight:** TuLugar is a **meta-aggregator**. Listings come from many sources (infocasas, century21, Clasipar, etc.). The `source_platform` field tells us where it was originally scraped from. They deduplicate via `source_content_hash`.
- **Verdict:** ✅ **SHIP**. Highest-leverage single source we found. Already de-duplicated across portals, pre-converted to USD, has lat/lon, has neighborhood. 15K+ listings per page × paginate = potentially 30K+ unique properties.

### 3.2 Encuentra24 Paraguay
- **URL:** https://www.encuentra24.com/paraguay-es/bienes-raices
- **Status:** ⚠️ SPA (Next.js). Sitemap returns HTML (broken), no JSON-LD, no public API endpoint that responds with JSON.
- **Scrape path:** Would need to inspect the JS chunks for the internal API, or use a headless browser.
- **Verdict:** Medium priority. TuLugar already aggregates some of these.

### 3.3 MercadoLibre Inmuebles Paraguay
- **URL:** https://inmuebles.mercadolibre.com.py/
- **Status:** ❌ Blocks non-browser User-Agents (403). Would require Playwright + cookies.
- **Estimated listings:** Few thousand (their UR-BR/AR sites have 100K+ but PY is small market).
- **Verdict:** Medium priority — only if TuLugar coverage proves insufficient. TuLugar already imports some.

### 3.4 Clasipar Paraguay
- **URL:** https://www.clasipar.com.py/
- **Status:** ⚠️ SSL cert mismatch on `.com.py`. Actual site is at `clasipar.com` (international). The `.com.py` returns cert error or redirect.
- **Verdict:** Skip. TuLugar already imports some.

### 3.5 Inmuebles Paraguay (inmueblespy.com)
- **URL:** https://inmueblespy.com/
- **Status:** ✅ HTML works, but no sitemap, no public API.
- **Verdict:** Low priority.

### 3.6 Century 21 Paraguay
- **URL:** https://century21.com.py/
- **Status:** ✅ HTML works (each property is a detail page).
- **Note:** TuLugar already imports century21.com.py listings — source_platform="century21.com.py" seen in TuLugar API.
- **Verdict:** Skip — already covered via TuLugar.

### 3.7 Properstar (international aggregator with PY inventory)
- **URL:** https://www.properstar.com/paraguay/buy
- **Coverage:** 3,524 PY listings, distributed: Asunción 1,287, Central 1,155, Cordillera 547, Itapúa 233...
- **Status:** ❌ sitemap.xml returns 429, /api/* returns 403, robots.txt returns 403. Heavy anti-scrape.
- **Verdict:** Skip unless TuLugar coverage is incomplete (unlikely).

---

## 4. 🏦 HOUSING FINANCE & BANKING

### 4.1 BCP — Estabilidad Financiera PDF
- **URL:** `https://www.bcp.gov.py/documents/20117/1058058/informe_IEF+may+2025_vf.pdf` (and similar quarterly URLs)
- **Size:** 1.3 MB
- **Auth:** None — direct download works
- **What it contains:** Banking system stability report, including:
  - Mortgage portfolio by bank (cartera hipotecaria)
  - Delinquency rates by loan type
  - Loan-to-deposit ratios
  - Real-estate exposure (inversiones inmobiliarias)
- **Verdict:** ✅ **SHIP**. Single PDF per quarter, can be downloaded and table-extracted. Add to a BCP bank-mortgage widget.

### 4.2 BCP "Situación General del Crédito" (quarterly)
- **URL pattern:** `https://www.bcp.gov.py/informe-sobre-situacion-general-del-credito-trimestral-i372` (and i373, i374, ...)
- **Status:** ❌ 403 blocked. Different anti-scrape policy than the PDFs.
- **Verdict:** Skip unless we can find the PDF behind it.

### 4.3 BNF — Banco Nacional de Fomento
- **URL:** https://www.bnf.gov.py/prestamos/prestamo-para-la-vivienda-fondos-propios-hipotecario-
- **What they have:** Housing loan programs ("Préstamo para la Vivienda Fondos Propios Hipotecario"). No public stats API.
- **Verdict:** ⚠️ Page-level scrape possible. Could pull their published mortgage rates.

### 4.4 CAH — Crédito Agrícola de Habilitación
- **URL:** https://www.cah.org.py/
- **Status:** ❌ DNS doesn't resolve (site gone or moved). Try `.gov.py` instead?
- **Verdict:** Skip.

### 4.5 AFD — Agencia Financiera de Desarrollo
- **URL:** https://www.afd.gov.py/
- **Status:** ❌ 403.
- **Verdict:** Skip.

### 4.6 INDERT — credit stats
- See 1.4.

---

## 5. 🛰 SATELLITE & LAND COVER (overlay context)

We already have these, but listing for completeness:

- **INBIO zafra** — 17 deptos × 3 crops (soja/arroz/maíz zafriña) ✅
- **NASA POWER** — 2024 climate for Asunción ✅
- **MapBiomas Paraguay** — 800MB land-cover raster download ⚠️ (would take 2-4 hours)
- **Hansen/JRC** — deforestation, planetarycomputer STAC auth ❌
- **NASA FIRMS** — active fires, free MAP_KEY needed ❌

---

## 6. 🏘 SHORT-TERM RENTAL (Airbnb & local)

### 6.1 Inside Airbnb
- **URL:** http://insideairbnb.com/get-the-data/
- **PY status:** ❌ **No Paraguay data**. Project covers US, AU, EU, Brazil, Mexico — no PY chapter yet.
- **Verdict:** Skip. Could use TuLugar listings flagged with `listing_type="short_rent"` as a partial substitute.

### 6.2 TuLugar has `listing_type` filter
- The API includes `listing_type="rent"` and `nightly_price`, `weekly_price`, `monthly_price` fields. This is enough to filter short-term rentals without Inside Airbnb.

---

## 7. 🚗 INFRASTRUCTURE & UTILITIES (context layers)

### 7.1 Geofabrik — road network
- **URL:** `https://download.geofabrik.de/south-america/paraguay-latest-free.shp.zip` (already downloaded in our `data/raw/geofabrik/`)
- **Status:** ✅ Includes roads/gis_osm_roads_free_1.shp
- **Verdict:** ✅ **SHIP NEXT** — extract roads, add as toggleable layer. ~5 min of work.

### 7.2 ANDE (electric utility)
- **URL:** https://www.ande.gov.py/
- **What they have:** No public geospatial data API.
- **Verdict:** Skip — would need PDF scraping for service-area stats.

### 7.3 ESSAP (water utility)
- Same story — no public API.
- **Verdict:** Skip.

---

## 8. 🗺 EXISTING DATA (already in our pipeline)

- Geofabrik admin: 18 deptos, 23 distritos, 1,278 barrios/localidades ✅
- Tile fabric 10×10 km: 7,912 cells ✅
- Priority tiles: 37 urban anchors ✅
- INBIO zafra 2025-2026 choropleth ✅
- GBIF species (200 records): 138 species ✅
- BCP macro/monetary snapshot ✅
- NASA POWER 2024 climate ✅
- 676 infocasas listings with full schema ✅
- 20 anchor cities ✅

---

## 📊 RECOMMENDED IMPLEMENTATION ORDER

### Wave 1 — Immediate (this week)
1. **Catastro Nacional WFS** → fetch + reproject + serve as GeoJSON tiles
   - Estimated records: 2.19M (too many for single file) → **tile into per-depto subsets**
   - First cut: 17 deptos × ~130K each = 17 files
   - Each file: `data/admin/catastro_<DEPT>.geojson` (~10-50MB each)
   - Add toggleable layer "Catastro parcels" with bbox filtering
   - Color by `valor_tierra` ($/m²) choropleth
2. **Catastro rural prices PDF** → parse to per-district reference table → add to insights
3. **BCP IEF PDF** → extract housing-mortgage table → new widget
4. **Geofabrik roads.shp** → extract → new toggleable layer
5. **TuLugar `/api/listings`** → fetch 15K listings (replace or augment our 676 infocasas ones)
   - Single bulk API call, paginated
   - Filter: `country=paraguay`, `status=active`
   - Output: `data/properties_tulugar.geojson` (~15-25MB)

### Wave 2 — Next sprint
6. **INBIO × Catastro overlay** — for each parcel, what crop is growing there?
7. **Property dedup pass** — match TuLugar listings to Catastro parcels by lat/lon proximity → get official `valor_tierra` per listing
8. **Encuentra24 scrape** — only if TuLugar coverage gaps
9. **MercadoLibre via Playwright** — only if needed

### Wave 3 — Future
10. **MapBiomas PY land cover** — 800MB raster, process once and tile
11. **NASA FIRMS active fires** — needs MAP_KEY (5min signup)
12. **Airbnb proxy via TuLugar nightly_price**
13. **Hansen/JRC deforestation via Planetary Computer** — needs auth token

---

## 🔧 TECHNICAL NOTES FOR IMPLEMENTATION

### Catastro WFS — coordinate reprojection
The CRS is **EPSG:32721 (UTM Zone 21S)**. WGS84 is EPSG:4326. To request in WGS84, add `&srsName=urn:ogc:def:crs:EPSG::4326` to the query (GeoServer auto-reprojects).

### TuLugar API — careful pagination
- Limit cap is **100 per page** even if you ask for 500.
- Offsets 0–11500 return 100 items each.
- Need to detect end-of-data (empty response or response without `data` key).
- Estimate: 15000 / 100 = **150 paginated requests** = ~5 minutes total at 1 req/sec.

### Rate limits / ethics
- Catastro WFS: no documented rate limit; recommend 0.5s between requests
- TuLugar: no documented rate limit; recommend 1s between requests
- infocasas: already proven at 0.5s

### Storage estimate
- Catastro per-depto: ~30MB × 17 deptos = ~500MB raw GeoJSON → after simplification: ~80MB
- TuLugar full dump: ~50MB GeoJSON
- Total addition to public/web/data: ~150-200MB

### Browser-side rendering
- 2.19M parcel polygons is too many to send to the browser. Use bbox-based dynamic fetching:
  - Map bbox changes → fetch only parcels in viewport (via WFS bbox filter)
  - Or pre-tile per-priority-tile (37 tiles × ~60K parcels each = ~2M, fits 37 small files)
- Alternative: pre-tile by departamento (17 files, ~130K each)

---

## ✅ ACTION ITEMS

I recommend we ship in this order:
1. **Wave 1.1 (Catastro per-depto tiles)** — highest value, 2.19M records
2. **Wave 1.2 (TuLugar listings 15K)** — replaces our 676 with 22× more, also adds $/USD auto-conversion
3. **Wave 1.3 (BCP mortgage widget)** — small but adds finance context
4. **Wave 1.4 (Geofabrik roads)** — easy win for visual context

Each can be done in ~1-2 hours with proper fetcher scripts + viewer wiring.

**Want me to start with Catastro Nacional WFS?** It's the single biggest dataset we'll ever pull into this project.