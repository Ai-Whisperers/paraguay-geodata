# Paraguay Geodata — Where To Work Next (2026-08-03)

Honest audit of the current state, what still needs work, and a prioritized
list of areas that would meaningfully improve the project.

## TL;DR — what is real vs what is fictional

After deploying 5 commits in the last round, the site works but the
**narrative** lags behind the data. Five concrete gaps block the next
jump in user value:

| # | Gap | Why it matters | Effort |
|---|---|---|---|
| 1 | **Home page shows 5,784 properties — actually 10,780** | Wrong number on the front door. Also wrong in meta description, og:description, JSON-LD. | 1 hr |
| 2 | **Guaraní (gn) is 0% complete in i18n.js strings** | Site claims 4 locales; only 3 of 4 are real. The 4th is essential because Guaraní is one of Paraguay's two official languages. | 1 day (or $200 translator) |
| 3 | **44% of listings use city-centroid fallback coords** (4,793 listings) | Map stacks 50-282 dots on top of each other in Asunción, Central, etc. The "real coords" stat in the project dropped from 100% to 35% in the coverage push. | 1-2 weeks |
| 4 | **41% of listings have no area (4,453 listings)** | Filter "min area" only works for 59% of inventory. People searching "min 1ha" miss the right listings. | 1-2 weeks |
| 5 | **No address extraction** (street + number) | The cross-source dedupe can only see 50 real duplicates because we don't have addresses. With addresses, the count would jump to 200-500. | 1 week |

## Live state — measured, not estimated

```
Listings:           10,780
Sources:            4 (asuncion_estate 7,383 · tulugar 2,038 · infocasas 1,156 · inmueblespy 203)
Active deptos:      19 (but 1,165 listings have no depto — "?" deptos)
Median freshness:   1 day
Tests passing:      150 / 152
Live commit:         6c4a88d
Cross-source dupes:  50 clusters, 101 merged
```

```
Data quality (the truth):
  4,793 listings (44.5%) have city-centroid coords (not real lat/lon)
  4,453 listings (41.3%) have no area_ha
  2,588 listings (24.0%) have no images
  1,183 listings (11.0%) have no property_type
    701 listings  (6.5%) have no title
    515 listings  (4.8%) have no price
```

## The narrative gap

The home page hero text says:
> "5,784 propiedades en Paraguay"
> "Mapa interactivo de propiedades en venta y alquiler"
> "16 ciudades"
> "3 fuentes"

The actual data says:
> 10,780 properties (live: `data_freshness.json`)
> 18 deptos
> 4 sources

This is the same "site lies about itself" pattern from Round 2. The
project is overstating; the home page is 2 commits behind.

### Concrete numbers that are wrong on the live site

```
home: "5,784 propiedades"        → live: 10,780
home: "16 ciudades"               → live: 19 deptos, 5,184 localities
home: "3 fuentes"                 → live: 4 sources
home: "5,784 propiedades" in JSON-LD → live: 10,780
home: og:description says 10,898  → live: 10,780 (data drift)
home: og:description says 18 deptos → correct
home: meta says 7,912 tiles       → live: 7,912 (correct — no change)
```

## Areas to work on — ranked

### 1. **Fix the home page numbers (1 hr, no risk)** — START HERE

Edit `exports/web/index.html`:
- Replace 5,784 with 10,780 in hero text, JSON-LD, og:description, twitter:description
- Update "3 fuentes" → "4 fuentes"
- Update "16 ciudades" → "19 deptos, 246 distritos"
- The i18n.js key `home.tagline` should pull these from data_freshness.json, not be hardcoded. Fix by:
  1. Add a small render step: `updateHomeStats()` reads data_freshness.json + facets.json and rewrites the hero numbers
  2. Or: regenerate the hero text from a tool (`tools/build_home_stats.py`) and run it in the cron

Impact: removes the most embarrassing lie on the front door. Improves CTR (a "10,780 properties" hero is much more credible than "5,784"). Worth doing FIRST.

### 2. **Guaraní translation pass (1 day + $200)** — Tier 1.5

The site claims 4-locale support. Reality:
- es: complete (106 i18n keys + full page-content)
- en: complete (106 i18n keys + full page-content)
- pt: complete (106 i18n keys + full page-content)
- **gn: 0%** — the `gn` locale object exists in i18n.js but all values are Spanish

This is the single biggest "claimed vs actual" gap on the site. Paraguay is the only country in the Americas with **Guaraní as an official language alongside Spanish**, and 90% of the population speaks it. A "4-locale" site that has 0% Guaraní is insulting to the people who live there.

What needs translating: ~106 i18n keys + ~3 long-form page sections (faq, pricing, use-cases) ≈ 5,000 words total.

Approach: hire a native Paraguayan Guaraní speaker (Jopará-aware, since 90% of speakers use Guaraní-Spanish code-switching) for $200. Deliver a JSON file with translations. I integrate.

### 3. **Geocode the 4,793 centroid listings (1-2 weeks)** — Tier 2

The `enrich_missing_only` step falls back to city centroids for asuncion.estate listings whose detail pages don't expose `data-lat` / `data-lon`. This is 44% of all inventory.

**Why this matters more than anything else:**
- The map shows 50-282 stacked dots on Asunción city center — visually broken
- The cross-source dedupe can't find real duplicates for these (they all share the same coord)
- The "is_usd_stable" enrichment uses lat/lon to look up distance to roads/climate — wrong for centroids

**Approach:**
1. For each centroid listing, look at the **title** for street/address keywords
   - "Casa en Ycuá Satí y Lillo" → "Ycuá Satí y Lillo" (street)
   - "San Bernardino Casa 4 dorm" → "San Bernardino" (city only — still centroid, but better)
2. Geocode extracted addresses via Nominatim (free, 1 req/s rate limit)
   - 4,793 listings × 1s = 80 minutes, sequential
   - With caching, 80% will hit cache after the first 1,000 — much faster
3. Store results in `data/geocoded_addresses.json` (reused on next run)
4. Update canonical with the real coords

**Expected gain:** Real coords 35% → 80% of inventory. Map becomes usable. Cross-source dedupe jumps from 50 to 200+ clusters.

### 4. **Extract area from title (3 days)** — Tier 2.5

4,453 listings have no area. For many of these, the title contains the area:
- "Terreno de 1,000.59m² en Venta en San Bernardino" → 1000.59 m² → 0.10 ha
- "Casa 350 m² en Asunción" → 350 m²
- "Departamento 2 dormitorios Recoleta" → no area (skip)

Regex pattern (Spanish):
```
(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*(m²|m2|mts2|metros\s*cuadrados|hectareas?|ha\b)
```

Apply during canonicalize. Easy 3-day task. Gets area coverage 59% → 85%.

### 5. **Real-time webhook ingest (1 week)** — Tier 3

Already built `tools/webhook_ingest.py` but no source pushes to it. The next step is:
- Wire tucasa.com's API webhook to /api/v1/vitals
- Wire InfoCasas's listing-deleted webhook to the same
- Auto-remove stale listings (anything >14 days old without update)

Impact: from "every 1-3 days" to "minutes". Big UX win for the dashboard view.

### 6. **Mobile Lighthouse 90+ (1-2 weeks)** — Tier 3

Bundle is 327KB, 363KB third-party. Mobile 4G users get ~3.2s LCP.

What to do:
1. Inline critical CSS (move 14KB site.css inline, defer the rest)
2. Defer leaflet-pmtiles.js (only loaded when PMTiles layer is toggled)
3. Defer chart.js (only loaded on Insights tab)
4. Self-host Inter font (rsms.me has 2+ redirects; self-host = 30% faster)
5. Service Worker for offline tiles + JS (workbox-strategies)

Realistic target: 80 → 90 mobile score.

### 7. **Property type inference (2 days)** — Tier 3.5

1,183 listings have `property_type: "unknown"`. The taxonomy normalizer
handles 7 canonical types. For "unknown" we can guess from:
- `title` keywords: "casa" → house, "departamento" → apartment, "terreno" → land
- `area_sqm` size: >1,000 sqm → likely land; 50-200 → apartment
- `bedrooms`: 0 → land; 1-2 → apartment; 3+ → house
- `listing_type`: sale + 5+ ha → land; rent + 1-3 beds → apartment

This gets unknown → 0% in 2 days.

### 8. **Real-time price-stability badge (1 week)** — Tier 4

`is_usd_stable` enrichment exists but uses static FX. Should be dynamic:
- Read BCP tasa_change daily
- Mark listings as "USD stable" only if last 7 days FX change < 2%
- Surface in popup: "USD stable (FX Δ 0.5% this week)"

Nice but not critical. Already shipped with static data.

### 9. **What NOT to do (carried from PLAN_v2 + Round 1)**

- ❌ Real-time scraping — sources block
- ❌ Native mobile app
- ❌ AI fair-price model (R² = 0.017 — already removed/de-emphasized)
- ❌ B2B SaaS — wait for 1 paying customer
- ❌ Multi-cloud deploy — CF Pages is enough

## Recommended sequencing (next 4 weeks)

```
Week 1 (low effort, immediate wins):
  Day 1-2: Fix home page numbers (#1) — 1 hr
  Day 3-4: Hire translator, ship Guaraní (#2) — 1 day + $200
  Day 5:   Area extraction from title (#4) — 3 days but the regex is fast

Week 2 (geocoding):
  Mon-Wed: Build address-extractor from title (300 lines, 1 day)
  Thu-Fri: Geocode via Nominatim with caching (2 days)
  Weekend: Re-run cross-source dedupe with real coords

Week 3 (UX):
  Mon-Tue: Real-time price-stability (#8) — 1 week split
  Wed-Fri: Mobile Lighthouse pass (#6) — 3 days critical CSS + SW

Week 4 (monetization + stretch):
  Mon-Wed: Property type inference (#7) — 2 days
  Thu-Fri: Webhook ingest wiring (#5) — 1 week split
```

## Conclusion

The project is **B+** with 10K listings, cross-source dedupe, and
Lighthouse CI gate shipped. The next 4 weeks would push it to **A-**:

- B+ → A- requires fixing the home page numbers (immediate)
- A- requires 80% real coords instead of 35% (geocoding pass)
- A requires Guaraní translations (it's the official language of Paraguay)
- A+ requires Stripe checkout (already researched; $29 GeoJSON download is the obvious SKU)

What's in your hands: hire the Guaraní translator, decide if you want
to spend on Nominatim (free) or a paid geocoder (Mapbox ~$5/1k calls).

What's in mine: the 4 weeks of work above. Pick which ones to ship and
I'll execute.
