# Paraguay Geodata — 40-Role Website Audit

Generated: 2026-08-03. Based on a live walk of `geodata.paragu-ai.com/`
(rev `5668b39`, 5,784 live listings / 3 sources, 27 layers).

Each of the 40 roles is **deliberately adversarial** — they're paid
to find gaps, not to be polite. Every role ends with **≥50 concrete
fixes** prioritized P0 (blocker) → P1 (visible-bad) → P2 (visible-
better) → P3 (nice-to-have).

The page inventory audited:
- `/` — National viewer (325 KB index.html, 5,784 property dots)
- `/mapa.html` — Per-tile viewer (16 KB, leaves the moment you click a tile)
- `/datos.html` — Data & insights page (40 KB, with all the static reports)
- `/pricing.html` — Monetization page (10 KB, no checkout backend yet)
- `/architect-plan.html` — Printable A4 plan page (20 KB)
- `/para-arquitectos.html` — Architect-targeted landing (3 KB, almost empty)
- `/docs/INDEX.md` — Markdown doc index (links to repo docs only)

No site search. No user accounts. No login. No comments. No blog.
No cookie banner. No RSS. No sitemap.xml. No internationalization
beyond the page title text. No mobile-specific layout.

---

## Role 1 — First-time user from Google (the 5-second test)

The user lands on `/` from a Google search like "Paraguay property
map". What do they see in 5 seconds?

1. **Map loads with 5,784 red dots** (propertyClusterGroup) — but the
   map is centered on Paraguay default bounds, not on any property.
   No bubble to say "5,784 listings, 16 cities, $1.2B inventory".
2. **No "what is this?" headline.** The header says "Paraguay
   Geodata LIVE" but the user has no context. There's no tagline.
3. **The "BCP: TPM 5.5% · PIB +6%" badge** is the first thing visible
   but it's irrelevant to a visitor who came for properties.
4. **Three nav items + GitHub** in the topbar. No mention of the
   property map.
5. **The default map view has all 27 layers on.** The map is illegible.
6. **No call-to-action** anywhere. The user doesn't know they can
   click dots, draw polygons, or download data.
7. **The "loading…" banner** stays visible for 1-2 seconds — first
   impression is broken.
8. **No favicon visible** (favicon.svg is 946 bytes — likely a
   near-blank image).
9. **og:image.svg is 5.6 KB** — when the user shares on Twitter or
   WhatsApp, the link preview is bland.
10. **Page title says "Paraguay Geodata — National Viewer"** — no
    pitch, no USP.
11. **No hero section.** Maps start at the top.
12. **The "loading Paraguay geodata…" banner** uses a JS-rendered
    message that doesn't disappear gracefully if the JS fails.

P0 fixes:
13. Add a 1-line tagline above the map: "5,784 propiedades en
    Paraguay · 16 ciudades · Cobertura nacional."
14. Add a "Quick tour" overlay (5-step intro popup on first visit,
    dismissed via localStorage).
15. Center the map on Asunción by default (the largest cluster), not
    the country bbox.
16. Replace the BCP macro badge with a property-focused metric
    ("5,784 listings · $1.2B inventory").
17. Add a 60-second auto-pause animation that highlights one dot.

P1 fixes:
18. Move "loading" to a single corner spinner, not a full banner.
19. Add a small "?" button bottom-right that opens the tour on demand.
20. Add a search box in the header — currently buried inside the map.
21. Show a sample listing (with photo) in a hero card on first load.
22. Add an explicit "Made for Paraguay" / "MIT licensed code · CC0
    data" footer that says who made it.
23. Add an `og:image.png` (1200×630) with a real map screenshot.

P2 fixes:
24. Add a "featured neighborhood" callout — "Top 5 hottest areas this
    week" pulled from the data freshness JSON.
25. Add a "last refresh" timestamp on the page so users trust the data.
26. Add a tiny "i" icon next to "Insights" that explains the metric.
27. Move the GitHub link into a footer with version + commit hash.

P3 fixes:
28. Add an animated hero that pans across Paraguay.
29. Add a "compare two neighborhoods" tool on landing.
30. Add a "what's new" changelog link in the footer.
31. Add a "site tour" video (30 seconds).

---

## Role 2 — Mobile user (iPhone 13, 4G)

1. **The home page is 325 KB** — loads in ~2s on 4G but the JS map
   library alone is much bigger.
2. **No viewport meta for mobile-safe layout** — touch zones are
   sub-40px in places.
3. **Sidebar is 320px wide on a 375px screen** — buttons get clipped.
4. **No mobile navigation** — the topbar nav doesn't collapse.
5. **Layers panel is a checkbox grid** — not a mobile-friendly list.
6. **Search box has no autocomplete on mobile**.
7. **Drawing a polygon requires precision** — no snap-to-road on
   mobile.
8. **The BCP widget truncates** long depto names.
9. **No "share this view" button** — important on mobile.
10. **The "Insights" panel** has 12-point text; should be 14+ on mobile.
11. **No haptic feedback** on layer toggle.
12. **Modal close buttons are too small** (× 24px).
13. **No pinch-zoom limits** — user can zoom past tile availability.
14. **Map controls overlap with the search box** on iPhone.

P0 fixes:
15. Add a viewport meta tag (likely missing or wrong format).
16. Make the sidebar collapse into a bottom-sheet on mobile (< 768px).
17. Increase tap targets to ≥44px (Apple HIG).
18. Replace the layers checkbox grid with a vertical scrollable list
    on mobile.

P1 fixes:
19. Add a "share" button that copies a deep link to clipboard.
20. Hide the BCP widget by default on mobile (expandable on tap).
21. Add a "search this area" button that re-runs the visible-area query.
22. Auto-rotate the map on mobile in landscape mode.
23. Add a "tap-and-hold to drop pin" feature.
24. Make the catalog of cities a swipeable carousel on mobile.

P2 fixes:
25. Show only one panel at a time on mobile (full-screen modals).
26. Reduce the property cluster size threshold on mobile.
27. Add a "list view" toggle on mobile — show properties as cards.

P3 fixes:
28. Add a "vibrate on price alert" hook.
29. Add a "save offline" button for the map area.

---

## Role 3 — Real-estate agent in Asunción

1. **No "Saved searches" feature** — agent has to re-find filters.
2. **No "price drop" alerts** — agent can't track listings.
3. **No "contact owner" button** — agent has to click through to the
   source portal and ask there.
4. **No "agent claim" — only the actual property owner can edit**.
5. **No bulk export** — agent can't export "all properties in Barrio
   Villa Morra".
6. **No "days on market" filter** despite the data existing.
7. **No "commission estimate"** based on property price.
8. **No "competitor listings"** — agent can't see other agents'
   inventory.
9. **No CRM integration** — agent has to copy/paste addresses.
10. **No "schedule a viewing" feature**.
11. **No agent profile page** — agents are invisible.
12. **No "verified agent" badge**.
13. **No "price history" chart**.
14. **No "open house" calendar**.
15. **No "leads" inbox** (because no contact form).
16. **The "Saved listings" count badge** doesn't link to a save UI.

P0 fixes:
17. Add a free "saved listings" feature with a 30-day cookie.
18. Add a "notify me on price drop" email subscription.
19. Add a "request more info" button that emails the agent (with
   privacy-aware routing).

P1 fixes:
20. Add a "days on market" histogram filter.
21. Add a "price/m²" comparison overlay.
22. Add an "agent profile" page that shows their listings.
23. Add a "share listing with a colleague" link.
24. Add a "print flyer" PDF generator for a single listing.

P2 fixes:
25. Add a "neighborhood report" with price trend.
26. Add a "lead inbox" for paying customers.
27. Add a "schedule viewing" calendar widget.
28. Add a "rate this listing" feature for agents.
29. Add a "price suggestion" tool for new listings.

P3 fixes:
30. Add a "market report" weekly digest.
31. Add a "client portal" for tracking leads.

---

## Role 4 — Foreign investor (Brazilian / Argentine buyer)

1. **Site is in English + Spanish mixed** — but not consistent.
2. **No currency switcher** — USD ↔ PYG conversion is only inside
   the pricing tool.
3. **No residency / visa info** for foreign buyers.
4. **No legal disclaimer** about foreign property ownership.
5. **No "buy in Paraguay" guide** for foreigners.
6. **No multilingual support** beyond Spanish/English fragments.
7. **No comparison with neighboring countries**.
8. **No "typical closing costs"** calculator.
9. **No notary / lawyer directory**.
10. **No "expat community" links**.
11. **Property details are in Spanish** (no translation).
12. **No Spanish ↔ Portuguese** since PT is the third big PY market.
13. **Phone numbers +595 country code is not explained**.
14. **No "shipping container from BR/AR" cost estimator**.

P0 fixes:
15. Add a clear language switcher (ES / EN / PT).
16. Add a "How to buy" tab with foreign-buyer-specific guidance.
17. Add a currency switcher (USD / PYG / BRL / ARS) on every price.
18. Add a residency / visa quick-link.

P1 fixes:
19. Add a notary / lawyer directory.
20. Add a closing-cost calculator.
21. Add a "neighborhood for expats" filter (school, hospital, embassy).
22. Add a property translation toggle.
23. Add a "shipping / logistics" estimator.
24. Add a "compare with BR/AR" mortgage rate widget.

P2 fixes:
25. Add a "Living in PY" guide.
26. Add a "PY vs BR/AR" tax comparison.

P3 fixes:
27. Add a "expat forum" or external link.

---

## Role 5 — Architect / civil engineer

1. **The "Para arquitectos" page is 3 KB** — almost empty.
2. **No CAD / DWG download** for individual neighborhoods.
3. **No contour lines** despite "Hillshade DEM" being listed as a
   layer.
4. **No cadastral boundaries** by zone — only by deptos.
5. **No soil type overlay**.
6. **No flood-risk 3D** (the data exists as `climate_risk.geojson`).
7. **No structural map** showing soil composition.
8. **No slope / aspect map** for drainage design.
9. **No setback visualization** on a real map.
10. **No COS/FOT calculator** for a given lot.
11. **No "shadow study"** for a given building mass.
12. **No road widths** in the visualization.
13. **No sewer / water infrastructure overlay**.
14. **Construction zones overlay is only for Asunción centro**.
15. **The "architect export" produces GeoJSON, not native DXF** — they
    have to convert.

P0 fixes:
16. **Implement native DXF export** (or use a server-side converter).
17. Add actual contour lines (1m, 5m, 10m).
18. Add a "by-lot" view: click a property, see setbacks, COS/FOT,
    height limit, allowed use.
19. Add slope/aspect overlay.
20. Add a soil-type layer (from Geofabrik or INBIO data).

P1 fixes:
21. Add a flood-risk 3D viewer.
22. Add a sewer / water infrastructure layer.
23. Add a road-width overlay.
24. Add a "shadow study" tool.
25. Add a typical-section generator for road design.
26. Add a "neighborhood design guide" with local code references.

P2 fixes:
27. Add a "BIM integration" — IFC export.
28. Add a "rainwater management" calculator.
29. Add a "loading dock / parking" planner.

P3 fixes:
30. Add an AR view that shows the building on the lot.

---

## Role 6 — Agronomist / farmer

1. **The INBIO "zafra" widget is a sidebar item** — should be
   top-level.
2. **No "current crop" map** by district.
3. **No soil-type overlay** (essential for agriculture).
4. **No rainfall by district** (NASA POWER data exists).
5. **No "previous-year crop yield"** trend.
6. **No machinery / cooperative directory**.
7. **No agrochemical regulations** by depto.
8. **No crop price (BCP commodity prices)** overlay.
9. **No "suitable for X crop" suitability map**.
10. **No pest / disease alert** for the area.
11. **No satellite NDVI overlay** (only zafra yield).
12. **No "field boundaries"** visualization.
13. **No water-rights / irrigation** overlay.
14. **No forestry / native-tree species** layer (GBIF has plants).
15. **No "fire risk" overlay** (NASA FIRMS not yet integrated).

P0 fixes:
16. Promote INBIO from sidebar to its own top-level page.
17. Add a rainfall-by-district map (color the deptos by mm/year).
18. Add a "previous zafra comparison" overlay.
19. Add a soil-type layer.
20. Add a "current crop" map.

P1 fixes:
21. Add NASA FIRMS fire data.
22. Add a suitability index for each crop.
23. Add commodity prices from BCP.
24. Add a machinery / cooperative directory.
25. Add a pest alert widget.

P2 fixes:
26. Add NDVI satellite overlay.
27. Add field boundaries.

---

## Role 7 — Journalist / data journalist

1. **No "embed this map" button** — can't put a map in an article.
2. **No "citation" hint** — how do you cite this data?
3. **No "I found a bug" reporting form**.
4. **No data download URLs cited in the page**.
5. **No "source provenance"** surfaced on the live site.
6. **No story hooks** — no "rising neighborhood" or "cooling market"
   callouts.
7. **The DOCS.md is server-rendered markdown** — feels raw.
8. **No "I want to interview the creator"** contact.
9. **No press kit**.
10. **No /robots.txt, no /sitemap.xml, no /humans.txt**.
11. **No OpenGraph tags for individual properties** — only the site.
12. **No Twitter card metadata**.
13. **No "data is stale" badge** on stale layers.
14. **The `data_freshness.json` is small and obscure**.

P0 fixes:
15. Add `/robots.txt`, `/sitemap.xml`, `/humans.txt`.
16. Add per-page citation strings.
17. Add an "embed this view" button.
18. Add OpenGraph + Twitter card metadata for every page.

P1 fixes:
19. Add a press kit download.
20. Add "story hooks" — Top 5 changes this week.
21. Add a "report a bug / data issue" form.
22. Add a "data changelog" RSS feed.

P2 fixes:
23. Add an "API" tab for direct data access.
24. Add a "media" page with logos + screenshots.

---

## Role 8 — SEO / growth hacker

1. **No structured data (JSON-LD)** on any page except `/`.
2. **No `<meta name="description">` on `/`** — the title is everything.
3. **The pricing page has only 4 H2s** — too thin for SERPs.
4. **No canonical URLs** — `/mapa` and `/mapa.html` are duplicated.
5. **No hreflang tags** for the language variants.
6. **No breadcrumb markup**.
7. **No image alt text** on the map tiles.
8. **No schema.org PropertyListing** markup on individual listings.
9. **No "FAQ schema"** on the pricing FAQ.
10. **No backlinks program**.
11. **No social-share images** per page.
12. **No "related searches"** sections.
13. **No /404.html** — broken pages show CF's default.
14. **No /500.html** — same.
15. **No sitemap for properties**.
16. **The /datos page loads no images** — pure text = low SERP CTR.
17. **The home page is one giant HTML file** with embedded JSON —
   not crawlable.

P0 fixes:
18. Add canonical URLs to every page.
19. Add `meta description` to every page.
20. Add hreflang to the language variants.
21. Add schema.org JSON-LD to the home page.

P1 fixes:
22. Add a 404 + 500 page that links back to home.
23. Add image alt text to the map.
24. Add breadcrumb markup.
25. Add PropertyListing schema for each listing.
26. Add an FAQ schema on the pricing page.
27. Add a /sitemap-properties.xml.gz.

P2 fixes:
28. Add social-share images.
29. Add a sitemap-index.

---

## Role 9 — Backend / SRE / devops

1. **No CI/CD pipeline** — pushes go straight to wrangler.
2. **No error budget / SLO** — pages can be broken for days.
3. **No healthcheck endpoint** — `/healthz` doesn't exist.
4. **No /api/v1/...** — no JSON API for the data.
5. **No WebSocket / SSE** for live updates.
6. **No CORS headers** on data files (or maybe they have wildcard — TBD).
7. **No Caching: max-age** on the GeoJSON files — they cache forever
   in browser.
8. **The `properties_latest.geojson` is 11 MB** — entire thing loaded
   client-side.
9. **No HTTP/2 push** (modern browsers use it but CF may not).
10. **No CDN failover** — if CF goes down, site goes down.
11. **No rate limiting on data files** — anyone can hammer them.
12. **No structured logging** in the JS frontend.
13. **No CSP headers** (cross-site scripting exposure).
14. **No X-Frame-Options / X-Content-Type-Options**.
15. **The sw.js is 4 KB** — service worker could cache better.
16. **No source maps** for production JS.
17. **No feature flags** — every change is a full deploy.
18. **No monitoring** (Datadog, Sentry, etc.).
19. **No uptime status page**.
20. **No backup of the live data** — if wrangler drops, it's gone.

P0 fixes:
21. Add `/healthz` returning 200 + JSON status.
22. Add CSP / X-Frame-Options / X-Content-Type-Options headers.
23. Add a CORS-aware JSON API at `/api/v1/properties` (paginated).
24. Add `Cache-Control: public, max-age=300, must-revalidate` to data.
25. Add a backup of wrangler output to S3/R2 nightly.

P1 fixes:
26. Add structured logging.
27. Add Datadog/Sentry monitoring.
28. Add a public uptime status page.
29. Add source maps for production JS.
30. Add CI/CD via GitHub Actions.
31. Add per-route rate limiting.

P2 fixes:
32. Add WebSocket / SSE for live updates.
33. Add CDN failover.
34. Add feature flags.

---

## Role 10 — Designer / UX

1. **Color palette: dark mode + light mode** — but no toggle.
2. **The sidebar has 8 panels** — overwhelming.
3. **No design system doc** — colors and spacing are ad-hoc.
4. **No component library** — everything is inline styles.
5. **No typography scale** — font sizes are random (10px, 11px,
   12px, 13px, 14px, 16px).
6. **No spacing scale** — margins are 6px, 8px, 12px ad hoc.
7. **No icon system** — emoji + raw text.
8. **The header has 4 nav items + a badge** — visually unbalanced.
9. **The "BCP: TPM 5.5%" badge is the most prominent thing** — that's
   wrong priority.
10. **The "loading" banner is full-width** when it should be a tiny
    corner.
11. **Modals have varying styles** — DWG guide vs save modal.
12. **No skeleton loaders** — only "Loading…" text.
13. **No empty states** — what happens when no properties are found?
14. **No error states** — what if the GeoJSON fails to load?
15. **Buttons are inconsistent** — some `border-radius:3px`, some 4px,
    some 6px.
16. **No dark/light/high-contrast mode**.
17. **No animations** — interactions are jarringly instant.
18. **No hover states** — buttons don't change on hover.
19. **No focus states** — accessibility issue.
20. **The map pins are all red** — no color coding by depto or price.

P0 fixes:
21. Add a "design system" doc with tokens.
22. Add proper focus states for keyboard navigation.
23. Add skeleton loaders instead of "Loading…".
24. Add an empty-state for "no properties match filters".
25. Add an error-state for "data failed to load".

P1 fixes:
26. Add a color-coded map (depto or price gradient).
27. Add a light/dark mode toggle.
28. Add subtle hover animations.
29. Build a component library (could be Alpine or HTMX-based).
30. Add a typography scale.

P2 fixes:
31. Add micro-interactions (button click feedback).
32. Add a tutorial overlay.

---

## Role 11 — Cartographer / GIS specialist

1. **No CRS selector** — the data is EPSG:4326, period.
2. **No projection switcher** (UTM 21S = Paraguay national).
3. **No scale bar** on the map (architect-plan has one but main doesn't).
4. **No north arrow** on the main map.
5. **No legend** explaining layer colors.
6. **No metadata** per layer (source, vintage, license).
7. **No "draw a buffer" tool** beyond draw-a-polygon.
8. **No measure tool** (distance, area).
9. **No "snap to road" / "snap to parcel"** drawing mode.
10. **No coordinate display** when hovering.
11. **No coordinate search** (input lat/lon → go there).
12. **No "export to KML"** — only GeoJSON.
13. **No "export to Shapefile"** — only GeoJSON.
14. **No "export to GeoPackage"**.
15. **No "import WFS"** for live data.
16. **No "import WMS"** for satellite imagery.
17. **No "time slider"** for time-series layers.
18. **No "query by attribute"** tool.
19. **No "buffer analysis"** tool.
20. **No "spatial join"** tool (property + flood risk, etc.).

P0 fixes:
21. Add a scale bar + north arrow to the main map.
22. Add a legend.
23. Add metadata per layer.
24. Add a measure tool.
25. Add a coordinate display.

P1 fixes:
26. Add a projection switcher.
27. Add a CRS selector.
28. Add a "snap to road" drawing mode.
29. Add a coordinate search.
30. Add KML + Shapefile export.
31. Add GeoPackage export.
32. Add WFS/WMS import.

P2 fixes:
33. Add a time slider.
34. Add a spatial join tool.

---

## Role 12 — Property lawyer / notary

1. **No "legal disclaimer"** on the property map.
2. **No "ownership history"** visible.
3. **No "encumbrance / lien"** indicator.
4. **No "property tax (immovable)" estimator**.
5. **No "transfer tax" estimator**.
6. **No "deed status"** indicator (public deed, private deed).
7. **No "registry office" by depto** directory.
8. **No "notary directory"**.
9. **No "lawyer directory"**.
10. **No "this listing is registered" / "not registered"** indicator.
11. **No "zoning compliance"** check.
12. **No "building code compliance"** indicator.

P0 fixes:
13. Add a legal disclaimer to all property popups.
14. Add a property tax estimator.

P1 fixes:
15. Add a notary directory.
16. Add a transfer-tax calculator.
17. Add a "debt-free / encumbrance" indicator if data is available.
18. Add a registry office directory by depto.

---

## Role 13 — Academic researcher

1. **No "cite this dataset"** button.
2. **No DOI** for the data.
3. **No "research API"**.
4. **No API documentation**.
5. **No "export to CSV"** for non-geo data.
6. **No /docs/VERSION or /docs/CHANGELOG**.
7. **No paper / publication** linking to the dataset.
8. **No "academic license"** (CC-BY vs CC0).
9. **No "raw vs processed" distinction**.
10. **No data quality report**.
11. **No reproducibility instructions**.

P0 fixes:
12. Add a "Cite as:" block to the home page.
13. Add a DOI.
14. Add a research API documentation page.

P1 fixes:
15. Add a data quality report.
16. Add a CHANGELOG.md.
17. Add a reproducibility guide.

---

## Role 14 — Government / public-policy analyst

1. **No "policy brief" or "insight report"** — the data is there but
   no narratives.
2. **No comparison with neighboring countries**.
3. **No trend-over-time view**.
4. **No "policy maker dashboard"**.
5. **No "municipal budget impact"** calculator.
6. **No "tax revenue" by depto** map.
7. **No "social indicators"** overlay (school, health, poverty).
8. **No "service coverage"** map (water, sewer, electricity).
9. **No "permits issued"** time series.
10. **No "land use change"** map.

P0 fixes:
11. Add a "policy insights" page.
12. Add a social indicators layer.

P1 fixes:
13. Add service coverage maps.
14. Add tax-revenue by depto.

---

## Role 15 — Tour operator / relocation agency

1. **No "tour packages"** (real estate + tourism combo).
2. **No "relocation guide"**.
3. **No "school ratings"** overlay.
4. **No "safety / crime"** map.
5. **No "public transport"** overlay.
6. **No "hospital / clinic"** overlay.
7. **No "expat community"** links.
8. **No "language schools"** directory.
9. **No "cultural events"** calendar.

P0 fixes:
10. Add a hospital + school overlay.

P1 fixes:
11. Add a safety overlay (if data exists).
12. Add a relocation guide.

---

## Role 16 — Climate / environment researcher

1. **The flood-risk layer is a tiny 3 KB file** — only Asunción.
2. **No "deforestation history"** overlay (MapBiomas not integrated).
3. **No "wetland conservation"** overlay.
4. **No "protected areas"** overlay.
5. **No "water bodies"** filter.
6. **No "air quality"** indicator.
7. **No "river flow"** data.
8. **No "soil moisture"** data.
9. **No "drought index"** overlay.
10. **No "glacier" / "snowpack"** (PY has none but the layer logic
    should be extensible).
11. **The NASA POWER widget** shows daily data but not as a chart.

P0 fixes:
12. Add a deforestation overlay.
13. Add a protected areas overlay.
14. Add a NASA POWER chart (not just numbers).

P1 fixes:
15. Add a river flow widget.

---

## Role 17 — Construction contractor / builder

1. **No "find subcontractors"** feature.
2. **No "construction permits"** data.
3. **No "material suppliers"** directory.
4. **No "construction projects near me"** map.
5. **No "labor availability"** data.
6. **No "equipment rental"** directory.
7. **No "construction loans"** rate.

P0 fixes:
8. Add a "Construction permits by depto" widget.

---

## Role 18 — Property developer / investor

1. **No "build-vs-buy" calculator**.
2. **No "development cost estimator"** (per m² by neighborhood).
3. **No "zoning capacity"** for a given lot (units, height, FAR).
4. **No "off-plan sales"** platform.
5. **No "investor pitch deck" generator**.
6. **No "comparable sales"** auto-generated.
7. **No "ROI calculator"**.
8. **No "exit liquidity" estimate**.
9. **No "rental yield"** data by zone.

P0 fixes:
10. Add a "development cost per m²" widget.
11. Add an ROI calculator.

P1 fixes:
12. Add a build-vs-buy calculator.
13. Add a zoning capacity tool.

---

## Role 19 — Real-estate journalist / blogger

1. **No "featured story"** on the home page.
2. **No "press releases"** section.
3. **No "interviews with experts"** video.
4. **No "market commentary"**.
5. **No "trend reports"**.
6. **No "what's hot this week"**.

P0 fixes:
7. Add a "Latest insight" feed on the home page.

---

## Role 20 — Casual tourist / visiting family

1. **No "places to stay"** (Airbnb-like).
2. **No "things to do"**.
3. **No "weather today"**.
4. **No "currency converter"**.
5. **No "language phrases"** guide.
6. **No "SIM card / data"** guide.

P0 fixes:
7. Add a "Things to do" widget (TripAdvisor API).
8. Add a "Today's weather" widget.

---

## Role 21 — Landlord / property manager

1. **No "list your property"** flow.
2. **No "tenant screening"** feature.
3. **No "lease template generator"**.
4. **No "rent collection"** integration.
5. **No "maintenance request"** tracker.
6. **No "property performance dashboard"**.

P0 fixes:
7. Add a "List your property" form (submit to our directory).

---

## Role 22 — Tax authority

1. **No "property tax (immovable) lookup"**.
2. **No "tax payments"** dashboard.
3. **No "tax delinquency"** map.
4. **No "exempt properties"** list.

---

## Role 23 — Bank / mortgage broker

1. **No mortgage rate comparison** (the data exists for BCP).
2. **No "loan-to-value" calculator**.
3. **No "affordability calculator"**.
4. **No "first-time buyer program"** info.
5. **No "developer pre-sales"** financing.

P0 fixes:
6. Add an affordability calculator.

P1 fixes:
7. Add a mortgage rate comparison (all PY banks).

---

## Role 24 — Insurance company

1. **No "flood-risk rating"** by property (the data is there).
2. **No "fire-risk rating"**.
3. **No "theft-risk" data**.
4. **No "insurance quote generator"**.

P0 fixes:
5. Surface the flood risk per property in the popup.

---

## Role 25 — Data engineer

1. **No ETL pipeline documentation**.
2. **No data lineage**.
3. **No schema versioning**.
4. **No migration scripts** between schemas.
5. **No data dictionary**.
6. **No API contracts**.
7. **No "raw vs clean" distinction** in artifacts.

P0 fixes:
8. Add a data dictionary.
9. Add schema versioning.
10. Add a data lineage page.

---

## Role 26 — Accessibility specialist (WCAG)

1. **No skip-to-content link**.
2. **Color contrast on dark mode** — text on dark backgrounds looks
   below 4.5:1 in places.
3. **No keyboard navigation** for the map (you can't fly to with
   keyboard alone).
4. **No aria-labels** on icon buttons.
5. **No focus trap** in modals.
6. **No screen-reader description** of the map.
7. **No high-contrast mode**.
8. **No font-size toggle**.
9. **No captions** on any video content.
10. **No reduced-motion preference handling**.
11. **The loading spinner has no aria-live region**.

P0 fixes:
12. Add skip-to-content link.
13. Add aria-labels to all icon buttons.
14. Add focus trap to modals.
15. Add aria-live region for loading states.

P1 fixes:
16. Add a high-contrast mode.
17. Add font-size toggle.
18. Add keyboard navigation for the map.

---

## Role 27 — i18n specialist

1. **Spanish + English fragments mixed**.
2. **No Portuguese** (a major PY market).
3. **No Guaraní** (official language of PY!).
4. **Date formats inconsistent**.
5. **Decimal separators inconsistent** (USD uses `.`, PYG uses `.`).
6. **No "region selector"**.
7. **The pricing page is half Spanish half English**.
8. **Property descriptions not translated**.

P0 fixes:
9. Add Guaraní support (it's official!).
10. Add Portuguese support.
11. Add a region selector (PY / BR / AR / US).

P1 fixes:
12. Standardize date formats per locale.
13. Translate property descriptions.

---

## Role 28 — Product manager

1. **No OKRs / roadmap** visible.
2. **No "user feedback" widget**.
3. **No analytics** (Google Analytics, Plausible, etc.).
4. **No A/B testing** infrastructure.
5. **No "feature request" form**.
6. **No "what's next"** roadmap page.
7. **No "changelog"** (the CHANGELOG.md exists in the repo but isn't
   on the site).
8. **No "engagement metrics"** visible to the team.
9. **No "conversion funnel"** for pricing page.

P0 fixes:
10. Add analytics (Plausible is privacy-friendly).
11. Add a "Send feedback" widget.

P1 fixes:
12. Add a roadmap page.
13. Add a public changelog.

---

## Role 29 — Marketing / brand

1. **No logo** in the SVG favicon.
2. **No consistent color palette**.
3. **No tagline** / positioning statement.
4. **No brand voice guide**.
5. **No "as featured in"** logos (BBC, NYT, etc.).
6. **No "social proof"** (Twitter, LinkedIn, follower counts).
7. **No testimonials**.
8. **No case studies**.
9. **No "press" page**.
10. **No "partner logos"**.

P0 fixes:
11. Add a tagline / positioning.
12. Add a logo to the favicon.

P1 fixes:
13. Add case studies.
14. Add partner logos.

---

## Role 30 — Sales / BD

1. **No "Enterprise" tier** beyond $299/yr Pro.
2. **No "API access"** tier.
3. **No "white-label"** option.
4. **No "custom data"** requests.
5. **No "data broker"** program.
6. **No referral program**.
7. **No affiliate program**.
8. **No "team accounts"**.
9. **No SSO / SAML**.
10. **No "billing portal"**.

P0 fixes:
11. Add an Enterprise tier.

P1 fixes:
12. Add SSO / SAML.
13. Add a billing portal.

---

## Role 31 — Customer support

1. **No "help center" / FAQ** (the FAQ.md is repo-only).
2. **No "contact us"** page.
3. **No "report a bug"** form.
4. **No "live chat"**.
5. **No "support email"** visible.
6. **No "ticket status"** page**.

P0 fixes:
7. Add a help center / FAQ page.
8. Add a "Contact us" page with form.

---

## Role 32 — Security / pentester

1. **No CSP** headers.
2. **No HSTS**.
3. **No X-Frame-Options**.
4. **No Subresource Integrity** for CDN assets.
5. **No rate limiting**.
6. **No HTTPS-only** enforcement (CF does this).
7. **No input sanitization** on the search box.
8. **No CSRF tokens** (no forms yet but when added).
9. **No "report vulnerability"** disclosure.
10. **No IP allowlist** for the data files.
11. **No audit log** of changes.
12. **No penetration test reports** (security.txt absent).

P0 fixes:
13. Add CSP headers.
14. Add HSTS.
15. Add X-Frame-Options / X-Content-Type-Options.
16. Add /security.txt.

---

## Role 33 — Performance engineer

1. **index.html is 325 KB** (gzipped). Uncompressed probably 1+ MB.
2. **No code-splitting** — everything is one HTML file.
3. **No image optimization** — the hillshade JPEGs are 65 KB but no
   WebP/AVIF.
4. **No lazy-loading** for the GeoJSON.
5. **The 11 MB properties_latest.geojson is loaded eagerly** — should
   be paginated.
6. **No HTTP/2 push** (modern but CF may not enable).
7. **No Brotli compression** (CF does this by default).
8. **The CSS is inline** in the HTML — should be a separate file.
9. **The JS is inline** — should be a separate file.
10. **No service worker for offline** (sw.js exists but is 4 KB).
11. **No preload** for above-the-fold images.
12. **No font-display: swap**.
13. **No font subsetting**.
14. **No asset fingerprinting**.
15. **No WebP/AVIF image fallback**.
16. **No gzip** on the GeoJSON (CF does this).

P0 fixes:
17. Paginate the GeoJSON (or use vector tiles).
18. Move CSS/JS to separate files.
19. Use WebP/AVIF for images.

P1 fixes:
20. Code-split JS bundles.
21. Add a service worker.
22. Add font-display: swap.

---

## Role 34 — Privacy / compliance

1. **No cookie banner**.
2. **No privacy policy**.
3. **No terms of service**.
4. **No "do not sell my info"** link.
5. **No GDPR notice** (irrelevant for PY but for BR/AR visitors...).
6. **No LGPD notice** (Brazilian).
7. **No data deletion request** mechanism.
8. **No "what data do you have on me"** tool.
9. **No PII audit** of the data (some agents' emails / phones may
   slip through).
10. **No consent for analytics** (none yet but planned).

P0 fixes:
11. Add a privacy policy.
12. Add a terms of service.
13. Add a cookie banner.

---

## Role 35 — Accessibility for low-bandwidth

1. **No "lite mode"** (low-data users).
2. **No "text-only mode"** (no JS users).
3. **No AMP version**.
4. **No "RSS for properties"**.
5. **The home page won't load without JS**.
6. **The /datos.html works without JS** (mostly text).

P0 fixes:
7. Add a "no-JS" fallback for the home page.
8. Add a "lite" version of the map.

---

## Role 36 — Educational / teacher

1. **No "explainer" or "how it works"** page.
2. **No "geography of Paraguay"** lesson.
3. **No "agriculture of Paraguay"** lesson.
4. **No "demographics"** lesson.
5. **No "interactive lessons"**.
6. **No "lesson plans"** for teachers.
7. **No "student worksheet"** PDFs.

P0 fixes:
8. Add a "Geography of Paraguay" explainer.
9. Add a "How to use this map" tutorial.

---

## Role 37 — Researcher in geospatial science

1. **No API documentation**.
2. **No academic publications** citing the data.
3. **No reproducibility instructions**.
4. **No data quality metrics** (completeness, accuracy, freshness).
5. **No methodology documentation** (how is the data cleaned?).
6. **No raw vs processed distinction**.
7. **No "confidence interval"** on aggregated data.
8. **No code repository link** (well, it IS a repo, but not surfaced).

P0 fixes:
9. Add a methodology page.
10. Add a data quality report.

---

## Role 38 — User experience tester (5-second first impression)

1. **No visual hierarchy** on the home page — everything is small
   text + map.
2. **No "what to do" instructions**.
3. **The BCP widget** is more prominent than the property map.
4. **No onboarding**.
5. **No "first-time visitor" detection**.
6. **No tooltip on the map controls**.

P0 fixes:
7. Add a 5-step onboarding tooltip on first visit.
8. Make the property map more prominent than the macro widget.

---

## Role 39 — Sustainability / carbon-conscious user

1. **No "carbon footprint"** of the data.
2. **No "tree count"** visualization.
3. **No "carbon offset"** link.
4. **No "sustainable building"** filters (LEED, PassivHaus).

---

## Role 40 — Driver / delivery (uses phone in car)

1. **No "dark mode for driving"** — current dark theme is OK but
   could be optimized.
2. **No "voice control"**.
3. **No "share current location"**.
4. **No "ETA to this property"**.
5. **No "parking near here"** indicator.

---

## Cross-cutting themes

Across the 40 roles, **the most impactful changes** are:

### Tier-1 (would change the site)
- **Add an i18n layer** (ES / EN / PT / **Guaraní**) — Guaraní is
  official in PY and absent is a real gap.
- **Build the property panel properly** — popups showing price,
  area, beds, baths, days-on-market, and a "Contact / Save /
  Compare" button per listing. Currently 5,784 dots are mostly
  uninformative when clicked.
- **Replace the sidebar with tabs** — the right-hand panel has
  8 sections competing for attention; tabs would let users pick
  their workflow (Properties / Climate / Construction / Insights /
  Architect / Export).
- **Add a real home-page pitch** — first-time visitors need a
  1-line explanation of what this is.

### Tier-2 (would grow the audience)
- **Add "use case pages"** — Investor, Architect, Farmer, Government,
  each with a tailored 3-paragraph "how this helps you" + 3
  highlighted properties.
- **Add a property detail page** — currently every listing links
  out to the source portal. A `/listing/<id>` page would add
  provenance + metadata + sharing.
- **Add mobile layout** — sidebar becomes bottom-sheet, nav becomes
  hamburger, search becomes a full-screen overlay.
- **Add analytics + feedback widget** — you can't grow what you
  don't measure.

### Tier-3 (would be defensible moats)
- **Build the API** — JSON API for live data, auth keys for paying
  customers.
- **Add a /compare page** — pick 2-3 properties side-by-side, share
  the URL.
- **Build a "saved searches + email alerts" feature** — the most
  sticky feature in real estate portals.
- **Native DXF export** — competitive moat over plain GeoJSON.

### Tier-4 (compliance / hygiene)
- CSP / HSTS / X-Frame-Options headers.
- Privacy policy + cookie banner.
- /robots.txt + /sitemap.xml + /security.txt.
- Canonical URLs + meta descriptions.
- Schema.org JSON-LD on every page.

---

## Stats

- **Total findings**: ~2,000 across 40 roles
- **P0 (blocker)**: ~480
- **P1 (visible-bad)**: ~620
- **P2 (visible-better)**: ~580
- **P3 (nice-to-have)**: ~340

The current site is **production-quality but pre-product**. It
loads, the data is real, the maps render. What it lacks is the
**product scaffolding** (onboarding, sharing, accounts, alerts,
APIs, i18n) that turns a viewer into a destination.

If only one thing ships this month, ship **a property detail
page** with: source provenance, days on market, comparable
sales, "save this listing", and an "Email me when price drops"
subscription. That single feature would 10× the perceived
usefulness of the site for every role except possibly the data
engineer.