# Additional insights for listings — 100-role audit

**Generated:** 2026-08-03
**Method:** Adversarial analysis by 100 simulated personas (buyers, professionals, regulators, researchers, devs) of the live canonical_properties.geojson (5,844 listings × 34 fields) plus the live site.

## Top-line numbers (raw data state)

| Metric | Value | Notes |
|---|---|---|
| Total listings | 5,844 | 4 sources (infocasas 1,156 / tulugar 2,038 / asuncion_estate 2,590 / inmueblespy 60) |
| Median price | $89,041 USD | p25=$4,700, p75=$239,726 |
| Median area | 0.0 ha ⚠ | 5,453 small (<5 ha) vs 146 farms (≥50 ha). The 0.0 ha median is because Asunción lots are stored in m²; needs conversion. |
| Price outliers | 82 listings >$10M USD | 1 has $3,500,000,000 (3.5B USD) — clearly a units error (likely guaraníes mistakenly stored as USD) |
| Listings with `neighborhood` | 28.5% | only 1,663 / 5,844 |
| Listings with `parking_spaces` | 16.0% ⚠ | only 933 / 5,844 |
| Listings with `bedrooms` | 58.3% | mostly Asunción houses; rural land has no bedrooms |
| Listings with `images` | 87.7% | 5,126 — the rest can't be visualized |
| Listings with risk score | 1,592 / 5,842 (27%) | joinable to existing risk data |
| Listings with stale (>30 days) | 0 | the cron overwrites; older dropped |
| Clusters (≥3 listings within ~100m) | 406 | up to 114 in one cluster; not surfaced to UI |

## Five concrete UI fixes the listing popup is missing

1. **Per-listing risk badge** — risk data exists for 1,592 listings. The popup should show:
   - Climate risk (deforestation + drought, 2024 baseline, derived)
   - Flood zone flag (if listing is in one of 5 SEN zones)
   - Forest loss % (2020-2024 from PROYECTO PAIS if available)

2. **Days-on-market in popup** — `days_on_market.json` has by_depto stats, but the per-listing value is in `freshness_days`. Popup shows scraped date but not "23 days old" with comparison to depto median.

3. **Nearest comparable listings** — clusters already group nearby listings. Click "Show 5 similar in this cluster" → list them inline.

4. **Distance to key amenities** — `buildings_asuncion.geojson` (Asunción), `roads.geojson`, `water.geojson` already exist. Compute nearest_road_km, nearest_water_m, nearest_building_m and show in popup.

5. **Currency stability indicator** — listings with `currency: USD` are preferred by foreign buyers. Pop-up should show currency + a "USD-stable" badge.

## Cross-cutting data joins missing

| What | Why it matters | Cost to add |
|---|---|---|
| Listing → nearest road | rural buyers need road access | 4 hrs (spatial join with roads.geojson) |
| Listing → indigenous territory | regulatory / ethical | 2 hrs (point-in-polygon vs indigenous_territories.geojson) |
| Listing → flood zone | insurance underwriting | 1 hr (spatial join) |
| Listing → catastro parcel | title verification | 3 hrs (point-in-polygon vs catastro_parcels_sample) |
| Listing → building footprint (Asunción) | urban planning / architectural exports | 3 hrs |
| Listing → nearest GBIF species | environmental context | 2 hrs |
| Listing → nearest water body | waterfront flag | 1 hr |
| Listing → depto median $/m² | comparative valuation | 1 hr (groupby on the canonical) |
| Listing → DOM vs depto median | "is this stale?" | 30 min |
| Listing → nearest 3 comparables | "see similar listings" | 2 hrs (k-NN on cluster_id) |

**Combined: ~20 hours of work** → every listing gains 9 ambient data points.

---

# 100-role analysis

## Buyers & investors (10)

1. **First-time buyer** — affordability calc + mortgage estimate. *Calc exists (`window.Ge`) but form fields are missing in HTML. **FIX: add the form fields.***
2. **Family** — school/hospital proximity. *Need OSM amenity join. 4 hrs.*
3. **Retiree** — quiet-area + low-crime + hospital access. *Depto safety overlay needed.*
4. **Investor** — rental yield calc, comparables. *Gross/net yield is in `window.Ge` but not surfaced; clusters exist (406 dense clusters) but not surfaced.*
5. **Expat** — USD-stable prices + residency rules. *Surface `currency` field as badge.*
6. **Cash buyer** — direct-from-owner filter. *Add `has_agent` field, 1 hr.*
7. **Land flipper** — recently-reduced + DOM >90. *Has DOM data; needs "recently_reduced" signal from price_history.*
8. **Airbnb host** — STR regulation by depto. *External research; add layer.*
9. **Rural buyer** — internet + road access. *Need `nearest_road_km`, `internet_available`.*
10. **Luxury buyer** — finishes, $/m² normalized. *Need `$/m²` field, sqft normalization. 1 hr.*

## Real estate professionals (10)

11. **Agent** — CRM-lite, share with client. *Saved exists; needs share-link.*
12. **Broker** — market analytics by barrio. *Need $/m² by barrio surface.*
13. **Appraiser** — comparable sales within 500m. *Clusters exist; surface.*
14. **Property manager** — rent-specific dataset. *Don't have rentals (only sales).*
15. **Title researcher** — catastro parcel overlap. *Missing join.*
16. **Photographer** — image quality score + similar listings. *image_clusters.json has 5.5K clusters; not surfaced.*
17. **Marketing analyst** — channel performance. *Have source-platform; need dashboard.*
18. **Developer** — zoning-allowed use per parcel. *construction_zones has 4 Asunción zones.*
19. **Mortgage broker** — rate trends. *mortgage_reference.json exists; not surfaced.*
20. **Insurance underwriter** — flood + climate risk per listing. *Risk data exists for 1,592/5,842; needs join + UI.*

## Researchers & academics (10)

21. **Urban planner** — density heatmap + time series. *No time-series yet.*
22. **Economist** — housing price index by depto FX-adjusted. *Compute $/m² by depto.*
23. **Sociologist** — listing language concentration. *Field missing.*
24. **Environmental scientist** — listings within protected areas. *Missing join.*
25. **Public health** — hospital proximity. *Missing OSM join.*
26. **Transport** — commute time from listing. *Missing OSRM join.*
27. **Journalist** — owner concentration analysis. *`source_agent` only 28.5% populated.*
28. **Tax researcher** — IPT municipal tax rates. *External.*
29. **Linguist** — corpus of descriptions. *Mostly Spanish; field exists but not collected.*
30. **Data scientist** — dataset download endpoints. *Exists per-depto; needs splits.*

## Government & regulators (10)

31. **MH (Vivienda)** — affordable housing stock, déficit habitacional. *Need $/m² distribution by depto.*
32. **SET** — transactions vs cadastral value. *Need cadastre join.*
33. **BCP** — monetary policy impact on real estate. *Widget exists; needs historical series.*
34. **MOPC** — listings without road access. *Compute; flag.*
35. **INCOOP** — cooperative listings badge. *None.*
36. **INDERT** — untitled properties. *Flag; estimate.*
37. **SEN** — flood-affected zones live alert. *Layer exists; need live feed.*
38. **SENAVE** — protected area proximity. *Missing join.*
39. **Municipality** — building-permit cross-check. *Missing.*
40. **DNA (Customs)** — import/export zones. *Layer needed.*

## Lawyers & notaries (10)

41. **Escribano** — due-diligence checklist. *`runDueDiligence` exists; never called.*
42. **Title clearance** — liens per parcel. *Missing.*
43. **Foreign investment** — FIRB per depto. *Regulatory notes needed.*
44. **Inheritance** — long-DOM low-engagement. *Has DOM.*
45. **Divorce** — joint-asset flag. *cluster_id exists, not surfaced.*
46. **Tax appeal** — comparable lower prices. *Could be export.*
47. **Eviction risk** — rent listings. *No rentals.*
48. **Boundary dispute** — adjacent parcel flag. *Could compute.*
49. **Squatter risk** — un-built rural far from roads. *Compute.*
50. **Public deed registry** — diario oficial. *External.*

## Tech / data (10)

51. **Frontend dev** — bundle 139 KB, leaflet-pmtiles.js not loaded. **FIX: add `<script src="data/leaflet-pmtiles.js" defer>` to enable PMTiles (411 KB vs 11 MB).**
52. **Backend dev** — cron architecture, retry policy. *RUNBOOK.md exists; expand.*
53. **DevOps** — deploy atomicity. *CF Pages cache vs latest bundle. Use cache-busting deploy.*
54. **Security** — PII scrub + GDPR. *Takedown endpoint exists; add completeness test.*
55. **Performance** — LCP/CLS/INP metrics. *monitoring.js set up; need real-device data.*
56. **a11y** — screen reader, keyboard nav, focus. *Not audited. **Add ARIA roles + keyboard test.***
57. **i18n** — 4 locales, mostly Spanish UI. *Add i18n to all UI strings.*
58. **SEO** — meta tags, OG tags, sitemap. *Verify.*
59. **Mobile UX** — tap-target sizes. *Audit.*
60. **CSP** — 'unsafe-inline'. *Tighten to nonce-based.*

## Cross-cutting product (10)

61. **UX** — `tabs.js` HierarchyRequestError on init. **FIX: not blocking but should be.**
62. **UX** — insights panel sections empty until async load.
63. **UX** — "Hide flagged" filter — what does flagged mean? Add tooltip.
64. **UX** — Compare only 2-3 listings; no saved-search.
65. **UX** — alert() calls instead of showToast(). **FIX: 3 sites use alert() instead of showToast().**
66. **UX** — no breadcrumb / nav history.
67. **UX** — image viewer no zoom/pan.
68. **UX** — no keyboard shortcut to clear filters.
69. **UX** — geocoder only Photon, no Nominatim fallback.
70. **UX** — filterSource dropdown missing "all sources" option.

## Industry-specific (10)

71. **Rancher** — livestock, water rights. *Out of scope.*
72. **Industrial buyer** — port + energy. *Need data.*
73. **Commercial retail** — foot traffic. *External.*
74. **Office space** — rent/sqft, occupancy. *No commercial.*
75. **Hospitality** — STR permits. *Regulatory layer.*
76. **Logistics warehouse** — highway/port. *Spatial join.*
77. **Cooperative** — cooperative membership. *None.*
78. **Mining** — extractive zones. *Regulatory.*
79. **Renewable** — solar/wind sites. *External.*
80. **Forestry** — deforestation overlap. **Need: forest-loss layer join (currently in `architect_export.geojson` for 534 features).**

## Geographic / cultural (10)

81. **Indigenous liaison** — don't list inside indigenous territories. *28.5% neighborhood; add filter.*
82. **Heritage** — historic buildings. *None.*
83. **Border region** — 137 listings near Brazil/Argentina. *Distinguish them.*
84. **Tourism** — Iguazú/Yacyretá zones. *Flag.*
85. **Demographer** — population density. *External.*
86. **Linguist** — Guaraní UI 95% missing.
87. **Religious sites** — proximity. *OSM join.*
88. **School zones** — catchment. *OSM join.*
89. **Transit access** — bus stops + future metro. *OSM join.*
90. **Waterfront** — river Paraguay listings. **Add `is_waterfront` flag (water.geojson spatial join, 1 hr).**

## Strategic / business (10)

91. **Competitor** — MercadoLibre / Zonaprop. *NDA question.*
92. **Pricing** — $29/$99 paid, but 99% want free viewport exports. Test pricing.
93. **Lead-gen** — agent capture. *No.*
94. **Partnership** — embed official APIs. *No formal contact.*
95. **International** — Uruguay/Argentina. *6 mo work.*
96. **Fundraising** — impact story for grantees. *Needed.*
97. **Open data network** — OKFN, code for all_latam. *2-week sprint.*
98. **Media** — PR story. *Ready.*
99. **AI/LLM** — auto-summarize descriptions. *Easy add.*
100. **Green building** — LEED/EDGE tag. *Add.*

---

# Prioritized recommendations (10 highest-ROI)

| # | Action | Effort | Impact | Status |
|---|---|---|---|---|
| 1 | **Add missing calculator form fields** (yieldPrice/Rent/Costs/Result + mortValue/DownPct/Rate/Term/Result + affIncome/Debts/Pct/Result) | 2 hrs | High — unblocks 3 working functions | NEW |
| 2 | **Add 9 spatial joins per listing** (road_km, water_m, building_m, flood, climate, indigenous, catastro, GBIF, $/m²) | 20 hrs | Massive — every listing gains 9 fields | NEW |
| 3 | **Load leaflet-pmtiles.js in index.html** | 30 min | 11 MB → 411 KB | TODO |
| 4 | **Fix price outliers** (3.5B USD, etc.) — detect PYG-as-USD errors | 2 hrs | Data quality | NEW |
| 5 | **Surface risk badge in popup** (flood, climate, forest_loss) | 2 hrs | High for insurance / env scientists | NEW |
| 6 | **Add neighborhood geocoding** (only 28.5% have it; use reverse Photon) | 4 hrs | Boosts barrio analytics | NEW |
| 7 | **Replace alert() with showToast()** (3 sites: exportKML, showSavedListings) | 30 min | UX | NEW |
| 8 | **Add "USD-stable" badge** for `currency: USD` listings | 30 min | Expat UX | NEW |
| 9 | **Surface days-on-market comparison** in popup (vs depto median) | 1 hr | Buyer UX | NEW |
| 10 | **Cache-busting deploy** for canonical `geodata.paragu-ai.com` | 1 hr | Fixes stale-cache bug | NEW |

## Architectural changes worth considering

- **Listing-level enrichments** are the highest-ROI: 9 spatial joins × 5,844 listings = ~50K new data points, but all derived from existing geojson. This is **the** feature to ship in Q4.
- **Currency stability** (USD-denominated listings are a clear premium) is an underserved market signal.
- **Risk overlay in popup** turns every listing into an insurance/environmental asset.
- **Geocoded neighborhood** unblocks all barrio-level analytics (broker dashboard, market reports).
- **Spatial joins** are the cheapest way to expand what each listing knows — the data already exists in geojson form.

## What's NOT actionable (out of scope)

- Live deal feed (would require partnership with portals)
- Real-time mortgage rates (would require BCP API access)
- Foreign-buyer residency rules (regulatory, not data)
- Commercial / rental data (no source dataset)
- Crime statistics (no public dataset exists for PY at the deptos level)

## Committed to repo

`docs/research/100-role-audit.md` — this file. Last updated 2026-08-03.