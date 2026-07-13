# Paraguay Geodata — Gap analysis & opportunity matrix

Generated: 2026-07-13. Built on top of `fd44aa9` + 6 subsequent commits. 27 layers, 10,898 listings live.

## A. Crashes / broken behaviour (P0 — fix now)

| # | Problem | Why it matters | Fix complexity |
|---|---|---|---|
| **A1** | **Properties popup shows "—" for price 68% of the time** (440/647 listings have `price_usd=null`). | Users click red dots and see nothing useful. The 2 most-asked questions of a real-estate map ("How much?" "How much per ha?") have no answer for 2/3 of pins. | **M** — fix the price-extraction regex in the infocasas parser (already parses price for 207/647; the rest probably have "consultar precio" or hidden in HTML). |
| **A2** | **Properties popup header says "Property"** instead of the actual listing title. | Every dot looks identical in the popup. Even a 1-line title would 10× the perceived value. | **S** — the scraper doesn't capture `<title>` from the listing page; add 1 line to the parser. |
| **A3** | **No `depto` field in viewer properties.** All 640 dots render without department context. | Cannot colour-code by depto or sort by depto. | **S** — extract depto from URL or page HTML. |
| **A4** | **deploy-meta.json is stale** (commit `2b7ee12`, doesn't mention INBIO/Geofabrik/640 listings). | The "what's actually live?" file lies. | **XS** — re-run the meta-builder. |
| **A5** | **`attrs: {}` empty** — no bedrooms / bathrooms / address. | Real-estate maps live and die by these filters. | **M** — need to scrape the address bar from the listing page (currently skipped). |

## B. Untapped data the viewer already has but doesn't show (P1 — quick wins)

| # | Untapped data | Currently | Should be |
|---|---|---|---|
| **B1** | **640 properties × `area_ha`** (99.7% complete) | Just a number | **Heatmap layer** — colour dots by `$/ha` so the map shows price-per-hectare zones (the most-asked real-estate metric). |
| **B2** | **20 anchor cities × live listing counts within 30 km** | Sidebar list (already there!) | Map should show a **city radius circle** + count badge on hover. |
| **B3** | **BCP remesas data** ("Top depts: Central, Alto Paraná, Asunción, Itapúa, Caaguazú") | Buried in the JSON | Add a **remesas-by-depto bar chart** to BCP widget — exactly what BCP reports quarterly, perfect for overlay with INBIO soja data. |
| **B4** | **NASA POWER climate** (366 days × 3 params) | Only the yearly summary shows | Add a **monthly heatmap strip** (12 cols × 3 vars = 36 cells) so users see dry/wet season + summer/winter temps. |
| **B5** | **INBIO geographic observations** (drought in south PY, +1.4% soja nationally) | Hidden in widget footer | Promote to a **dedicated "Insights" panel** at the top of the sidebar. |
| **B6** | **NASA POWER + INBIO correlation** | Not joined | Overlay: where are the driest 2024 zones that ALSO had arroz/maíz losses in 2025-26? This is the most-asked agri question. |
| **B7** | **INBIO 2025-2026 vs previous zafras** | One snapshot | **Time-series strip chart** at the bottom — show last 5 zafras side-by-side (would need to parse 4 more INBIO PDFs, but parser already exists). |

## C. Untapped datasets we don't yet fetch (P2 — bigger wins)

| # | Dataset | Source | Effort | Value |
|---|---|---|---|---|
| **C1** | **DEXPAR / MIC remesas by depto** | BCP quarterly XLSX (currently 403) | M | High — direct correlation with INBIO, properties, BCP rates |
| **C2** | **INBIO historical series (2007-2024)** | 55 PDFs catalogued, parser ready | M | High — multi-year trend lines for soja/arroz/maíz |
| **C3** | **Casas de cambio FX rates** | BCP, BCP itself publishes daily | S | Medium — properties are listed in PYG/USD, real FX matters |
| **C4** | **Forest cover change (MapBiomas PY)** | mapbiomas.org | M | High — cross with INBIO to see deforestation → soja expansion |
| **C5** | **NASA FIRMS active fires** | NASA FIRMS API (needs MAP_KEY) | S | High — fire detection overlays last 24h-7d |
| **C6** | **OpenWeather / OpenMeteo current conditions** | open-meteo.com (no key) | XS | Medium — add a "now" overlay |
| **C7** | **Electricity service coverage by depto** | ANDE annual report | M | Medium |
| **C8** | **Road network (Geofabrik roads.shp, already on disk)** | /tmp/py_geofabrik | S | High — overlay routes + junctions, snap properties to roads |
| **C9** | **Health facilities + schools** | Geofabrik POIs | S | Medium |
| **C10** | **DGEEC demographics (population by depto/distrito)** | datos.gov.py (CF-blocked) | M | Medium-high |
| **C11** | **Election results by depto** | TSJE | M | Medium |
| **C12** | **DINAC weather stations (real-time)** | dinac.gov.py | M | High — replace NASA POWER centroid with real stations |

## D. UX / bug fixes the user would notice in 5 seconds (P1)

| # | Issue | Fix |
|---|---|---|
| **D1** | Layer list clipping ("GBIF Animalia" overlaps with widget label) | CSS `min-width: 170px` for the layer grid item |
| **D2** | Sidebar has 8 long sections — no scroll hint, no "back to top" | Add `scroll-snap-type` and a sticky top-of-sidebar summary |
| **D3** | The choropleth scaling shows Asunción departamento (which has 0 soja) as the darkest purple because all deptos get a non-zero `data.soja` from the index lookup | Fix: scale ratio to `soja / maxSoja`, but mark null/0 cells as "no data" |
| **D4** | Property dot radius (6px) doesn't vary with price — busy areas look identical to sparse ones | Add a small radius scaling (4-10px based on log price) |
| **D5** | No search/filter for properties by city, depto, or price range | Add 3 input fields above the city list |
| **D6** | No "show on Google Maps" deep link from property popup | Already 90% there (dept popup has it, property doesn't) |
| **D7** | Sidebar shows 8 "h2" headings with no collapsible behaviour | Make sections collapsible (sticky expand/collapse) |

## E. The 3 things I'd ship RIGHT NOW (in priority order)

### Ship-1 (P0): Property price/title/depto fix — 30 minutes
- Update `tools/fetch_properties.py` to:
  - Capture `<title>` from each listing detail page
  - Capture price from the inline `<script>__NEXT_DATA__</script>` JSON (most robust)
  - Capture depto from URL slug
- Re-run merge → properties_latest.geojson now has all 3 fields for ~95% of listings
- Re-deploy

### Ship-2 (P1): Property $/ha heatmap layer — 1 hour
- Replace the static red dots with **$/ha heatmap** using leaflet.heat
- Add a colour scale legend to the sidebar
- Add a toggle: "Heatmap on/off"
- This is the single most-asked real-estate question — answer it visually

### Ship-3 (P1): Insights panel — 30 minutes
- Add a top-of-sidebar "Insights" card that summarizes 5 derived facts:
  - "Drought signal: arroz −22% nationally, worst in Misiones (−38%)"
  - "Soja still expanding: +49,303 ha vs 2024-25"
  - "640 listings across 18 deptos, median ~$130K USD, $46,667/ha"
  - "BCP: PIB +6% 2025, TPM stable at 5.5%"
  - "Asunción cluster has 76 listings within 30 km (12% of all)"
- Auto-generated from the existing JSON data; no new fetches needed.

## F. Realistic "next 5 days" plan

| Day | Output |
|---|---|
| 1 | Ships 1-2-3 above → first heatmap. Page goes from "exploratory" to "useful". |
| 2 | INBIO historical series (5 zafras back = 5 more PDFs parsed) — enables multi-year chart. |
| 3 | NASA POWER monthly heatmap + correlation with INBIO arroz losses |
| 4 | DEXPAR remesas by depto (proper BCP integration, scrape the XLSX via Playwright if direct download 403s) |
| 5 | MapBiomas PY land cover 2023-24 change overlaid on soja / arroz / maíz choropleths — the "land-use story" view |

## G. What's already great (don't waste time)

- 10,000+ features live, viewer works, no console errors
- 5 working widgets (BCP, NASA, INBIO, Coverage, Status)
- 8 toggleable layers (incl. 2 sub-admin that need toggling)
- 20 anchor cities with proximity counts
- 1,289 admin polygons (deptos + distritos + barrios)
- Clean purple INBIO choropleth works (verified by vision)
- All endpoints return 200

---

## Items completed in this session (2026-07-13)

### Critical bugs fixed
- ✅ **Properties vanished at zoom >= 11** (clusterProperties early-return bug) — now renders individual markers
- ✅ **CSV export button missing** (function existed, no UI) — added to header, respects active filters
- ✅ **INBIO choropleth scale collapsed** — switched to P95 percentile scale
- ✅ **HTML <head> structurally broken** (regression from phase 0) — full reconstruction with og/twitter/manifest
- ✅ **Properties fetched 2x in code** — memoized with fetchPropertiesOnce()
- ✅ **Signals HTML rendered inline only once** — extracted to renderSignals() with refresh

### Features added
- ✅ **Saved listings** (localStorage) - Star Save button on popups, modal viewer
- ✅ **Theme toggle** (dark/auto/light) - persists in localStorage
- ✅ **Insights panel** at top of sidebar - live market signals with refresh
- ✅ **Collapsible sidebar sections** - <details open> with chevron
- ✅ **Print stylesheet** - clean B&W map printout, grayscale tiles
- ✅ **PWA install + service worker** - beforeinstallprompt handler
- ✅ **Keyboard nav in search** - ArrowUp/Down/Enter/Escape
- ✅ **Google Maps / OSM / Search deep links** in popups
- ✅ **Toast notification system** - success/error/info types
- ✅ **Anchor city circles** - 20 cities, 30 km radius, listing density
- ✅ **Heatmap overlays** - $/ha (green->red) and lot area (blue->yellow)
- ✅ **NASA POWER 12-month strip** - temp + precip chart
- ✅ **Price-radius scaling** - markers scale 3-14 px by log price
- ✅ **Advanced filters** - depto, city, source, sort
- ✅ **favicon.svg + og-image.svg** - referenced but missing

### A11y improvements
- ✅ **Skip-link to map** - appears on focus
- ✅ **Focus-visible outline** - 2px accent ring on keyboard nav
- ✅ **aria-live on loading banner**
- ✅ **More aria-label** on action buttons

### Pending (next session)
- Cloudflare Web Analytics token (placeholder ready)
- GN (Guarani) translations (currently ES fallback)
- No CI / no auto-deploy on git push
- No uptime monitor / error reporting
- No mobile bottom-sheet refactor for filters
- No chart export / share PNG
- Catastro distrito layer to fetch 268 features (currently 10)
- Distritos layer currently 10 (Paraguari only) - needs full WFS refetch
