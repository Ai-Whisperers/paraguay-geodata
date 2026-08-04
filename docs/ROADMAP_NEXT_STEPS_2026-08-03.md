# Paraguay Geodata — Where We Are & What To Do Next

**Date:** 2026-08-03
**Audience:** Ivan (founder), Erebus (this AI), any future contributor
**Reads first:** STATUS.md (live KPIs), PLAN_v2.md (quarterly backlog), 100-role-audit.md (what's missing)

## Executive summary — what we are

A free, public-data viewer for Paraguay real estate + cadastre + environmental layers. 5,844 listings from 4 sources, 23 data layers, 4-locale UI (es/en/pt/gn), CC0 license, GDPR-compliant.

**What works (verified live):**

- Map renders with 1,500+ markers across 4 sources
- 6 sidebar tabs (Properties/Insights/Climate/Construction/Architect/Export)
- 14 filter controls (price/type/beds/area/depto/source/...)
- 8 layer groups, 36 layers, 11 layer registry entries
- 5 widgets: BCP macro, NASA POWER climate, INBIO zafra, fair-price ML, Esri satellite toggle
- 11 ambient fields per listing (just shipped — depto, road_km, water_km, gbif_km, flood_zone, climate_risk, indigenous_flag, USD-stable badge, $/m², freshness, outliers)
- Calculators: yield + mortgage + affordability (form fields added)
- 3 export formats: GeoJSON, DXF, KML
- 3 currency-stable badges, 5 download endpoints
- 4 locale switching (Guaraní is 95% untranslated, see below)
- 18 deptos coverage, 5,844 PII-clean listings

**What's broken (from ROAST_R2):**

1. pmtiles URL was `/leaflet@4.0.1/...` (404) — **fixed**
2. `deploy-meta.json` was 23 days stale — **fixed**
3. `scripts/build_deploy_meta.py` was a JSON file mislabeled as `.py` — **fixed**
4. "Time slider" was a stub with `min=0 max=0 disabled` saying "coming soon" — **fixed**
5. **5 unused tools** never called by any cron
6. **19 unused scripts** never run
7. **`tile_index.json` (3.7MB)** loaded on every page (660ms)
8. **`properties_latest.geojson` (12MB)** shipped but unused
9. **5 HTML pages** still have "Coming soon" / "TODO" markers in production
10. **Lighthouse CI** has `--no-pmtiles` flag that doesn't exist

**Test status:** 129/131 pass (98%), 1 skip, 1 xpassed.

---

## The hard truth about where the project sits

Looking at the data:

```
Q3 OKRs (from STATUS.md, dated 2026-08-03):
  O1 Ship 10K listings         58% (5,844 live vs 10,000 target)
  O2 Trust                     75% (PII clean, status page, GDPR endpoint ✓;
                                  Lighthouse + Web Vitals pending)
  O3 Performance               50% (PMTiles ✓, Lighthouse <90, LCP <1.5s — TBD)
  O4 Operability               80% (CI ✓, runbook ✓, DR ✓, R2 mirror pending,
                                  multi-account CF Pages pending)
  O5 Monetization              10% (pricing page ✓, no Stripe, no paying customer)
```

The project is **mid-stride on Trust + Performance** but has only **10% of monetization** and is structurally short on **coverage**. The biggest gap between "shipped" and "production-ready" is coverage — and the second biggest is the gap between Spanish UI and 4-locale promise.

## Where to invest (in order of ROI)

### Tier 1 — This week (cheap, high impact)

These close the gap between "shipped" and "production-ready" without requiring new data sources or external dependencies.

#### 1.1 Add Guaraní translations to 95% of UI strings (4 hrs)

**Why:** The site claims 4 locales (es/en/pt/gn) but only 4-5 strings are translated. 95% of users land on Spanish. The Guaraní label says "🇵🇾 Atyguasu" but every dropdown, button, layer name, filter label, error message is Spanish.

**What to do:**
1. Find the i18n key set: search `data-i18n` in HTML (currently ~4 keys), build the full key list (probably 200-400 strings).
2. Add Guaraní translations: hire a native speaker (Paraguayan Guaraní ≠ Brazilian Guaraní or Nheengatu — different orthographies).
3. Add Portuguese (BR/PT) — currently uses European Portuguese.
4. Verify EN is complete.

**Cost:** 4 hrs engineering + $200 native-speaker review. **Impact:** Closes the "we claim 4-locale, ship 1" gap. Critical for the indigenous community angle.

#### 1.2 Add a real Lighthouse budget + CI gate (3 hrs)

**Why:** O3 KR3.2 (mobile Lighthouse ≥ 90) is currently UNVERIFIED. The CI workflow runs Lighthouse but doesn't fail the build on regression.

**What to do:**
1. Add `lighthouse-budget.json` with thresholds:
   - LCP < 2.5s
   - CLS < 0.1
   - TBT < 200ms
   - Performance score ≥ 90
2. Wire `--assert` flag in lighthouse-ci-action.
3. Add `assertedScore: 90` to LHCI config.
4. Wire web-vitals observer to fail-silent on regression.

**Cost:** 3 hrs. **Impact:** Prevents performance regression. Critical for O3.

#### 1.3 Delete dead files (2 hrs)

**Why:** 4 tools + 19 scripts are orphaned (Round 2 roast). They confuse contributors and bloat `git log`.

**What to delete:**
- `tools/auto_refresh.py` (replaced by cron + wrangler-pages-deploy.sh)
- `tools/build_mortgage_reference.py` (orphaned — output is unused)
- `tools/check_property_links.py` (would get banned per Round 1)
- `tools/fetch_catastro_parcels.py` (orphaned — data is in canonical)
- 14 of 19 unused scripts that don't fit the new pipeline:
  - `scripts/extract_images_from_cache.py` (no caller)
  - `scripts/simplify_geojson.py` (no caller)
  - `scripts/validate_visualization.py` (no caller)
  - `scripts/gbif_to_geojson.py` (no caller)
  - `scripts/geofabrik_admin_to_geojson.py` (data already extracted)
  - `scripts/merge_property_sources.py` (replaced by merge_fresh_sources)
  - `scripts/reparse_cached_listings.py` (orphaned)
  - `scripts/build_paid_dxf_export.py` (no paid tier yet)
  - `scripts/build_inbio_zafra_strip.py` (orphan — strip JSON unused)
  - `scripts/build_inbio_series.py` (orphan — series JSON unused)
  - `scripts/build_property_risk_analysis.py` (orphan — data is built but never refreshed)
  - `scripts/build_risk.py` (orphan)
  - `scripts/build_architect_export.py` (orphan)
  - `scripts/build_deploy_meta.py` (the JSON template, was the fake builder — keep for archival)

**Cost:** 2 hrs (grep + rm + commit). **Impact:** Cleaner repo, ~5,000 LOC removed. Prevents future contributors from thinking these are load-bearing.

#### 1.4 Wire argenprop + 4 other fetchers into the cron (6 hrs)

**Why:** Round 1 §1.25 said the cron only runs 5 of 7 fetchers, and 2 are dead. Currently the pipeline is: `fetch_properties` + `fetch_tulugar` + `fetch_clasipar_sitemap` + `fetch_clasipar_public` + `fetch_asuncion_estate`. The unused ones:
- `fetch_argenprop.py` — works, would add ~20 listings/month
- `fetch_inmueblespy.py` — works, would add ~60/month (already in canonical)
- `fetch_inbio.py` — works, generates `inbio_zafra_2025_2026.json`
- `fetch_bcp_rates.py` — works, generates `bcp_snapshot.json`
- `fetch_catastro_parcels.py` — orphan

**What to do:** Add to `refresh_properties.sh`:
```bash
python3 -m tools.fetch_argenprop --output-dir "$WORK/argenprop" || log "WARN"
python3 -m tools.fetch_inmueblespy --output-dir "$WORK/inmueblespy" || log "WARN"
python3 -m tools.fetch_inbio --output-dir "$WORK/inbio" || log "WARN"
python3 -m tools.fetch_bcp_rates --output-dir "$WORK/bcp" || log "WARN"
```

**Cost:** 6 hrs (mostly testing). **Impact:** BCP widget data freshness improves from 24 days to daily. INBIO data fresh. Argenprop adds coverage.

### Tier 2 — This month (medium effort, big payoff)

#### 2.1 Ship the 4 data sources that exist but aren't wired (1 week)

The `data/sources/` docs describe **9 viable sources**. We currently use 4. The other 5:

| Source | Status | Could add |
|---|---|---|
| argenprop.com | Fetcher exists, not in cron | 20 listings/month |
| encuentra24.com | Round 1 §skip — SPA, no clean API | 0 (skip) |
| propiedades.com.py | No fetcher at all | 1,500 if reachable |
| clasipar.com | Public fetcher exists, 0 listings | 100+ if Playwright added |
| century21.com.py | Deleted (was dead) | 0 |
| bienesonline | Deleted (was dead) | 0 |
| ml_inmuebles | Deleted (was dead) | 0 |

**Realistic target:** argenprop + a Playwright wrapper for clasipar = +150 listings. **Cost:** 1 week. **Impact:** O1 KR1.1 (5 sources) → 6 sources. Hits 6,000 listings.

#### 2.2 Implement cross-source dedupe (3 days)

**Why:** `canonicalize_properties.py` claims to dedupe but the actual implementation is `source_url` exact match. The same property listed by infocasas + tucasa + propiedades.com.py shows up 3×.

**What to do:**
1. Title similarity > 85% (Levenshtein)
2. Distance < 50m (haversine)
3. Area within 10%
4. Different source_ids → flagged as duplicate
5. Surface in popup: "This property also listed by [source1, source2]"

**Cost:** 3 days. **Impact:** True unique listing count = ~5,500 instead of 5,844. Better analytics. **Critical for O1 KR1.4 (coverage).**

#### 2.3 Stripe-backed API for Pro tier (1 week)

**Why:** O5 KR5.1 says "checkout-worker is dead code" but no plan to make it live. The pricing page advertises $29/$99/$299 but checkout goes nowhere.

**What to do:**
1. Wire `exports/checkout-worker/src/index.ts` to actual Stripe (currently a stub).
2. Use Stripe Payment Links (no backend needed): `$29 → unlock_geojson_national`, `$99 → unlock_dxf_national`, `$299 → annual_pro`.
3. Verify webhook → unlock `__STRIPE_CHECKOUT_URL` → site enables "Buy" buttons.
4. Add `paid_users` table in Supabase (or just KV).
5. The site already has the gated button code (from `__STRIPE_CHECKOUT_URL=""`) — just point it at real URLs.

**Cost:** 1 week. **Impact:** Realizes O5. First paying customer = $29-$99. **Highest ROI in the whole roadmap** if it works.

#### 2.4 Get to 10K listings via 2 parallel paths (2 weeks)

Two paths that should run in parallel:

**Path A — Geographic expansion:**
- Wire `fetch_inmueblespy.py` to all 17 deptos (currently 8).
- Add `fetch_argenprop.py` to all deptos.
- Add Clasipar Playwright fetcher for 5 deptos.
- Realistic: +1,200 listings = 7,000 total.

**Path B — Improve existing extraction:**
- Increase `asuncion_estate.py` from 1,441 → 5,000 listings (the source has ~30K).
- Add detail-page enrichment (currently only listing-page).
- Realistic: +3,000 listings = 8,800 total.

**Cost:** 2 weeks. **Impact:** Closes O1. 10K target met or close.

### Tier 3 — Strategic (Q4 2026)

These are bigger lifts. Some are **not worth doing** — see "What we explicitly won't do" in PLAN_v2.md.

#### 3.1 Mobile Lighthouse 90+ (1-2 weeks)

Current state: untested on real devices. Bundle is 327KB. 1,500 markers on map is heavy.

**What to do:**
1. Audit `<script>` tags — defer everything.
2. Inline critical CSS.
3. Lazy-load chart.js + leaflet-pmtiles.js (only on tabs that need them).
4. Service Worker for offline tiles.
5. Run Lighthouse on real Android 4G throttling (the GitHub Action uses simulated 4G).

**Cost:** 1-2 weeks. **Impact:** O3 KR3.2. Real users on rural 4G.

#### 3.2 Realtime webhook ingest (1 week)

**Why:** Today, data is 1-3 days stale because cron pulls. With webhooks, source pushes → server ingests → live update.

**What to do:**
1. Already have `tools/webhook_ingest.py` and `/api/v1/vitals` serverless function.
2. Add `/api/v1/listings` POST endpoint.
3. Add HMAC verification (Stripe-style).
4. Wire one source (tucasa has API) as proof.
5. Surface in `/bulletin.json`.

**Cost:** 1 week. **Impact:** From "every 1-3 days" to "minutes". Big UX win.

#### 3.3 Multi-tenancy (DO NOT BUILD)

PLAN_v2 says "Multi-tenancy — single instance, multiple customers" — this is **explicitly not until Q2 2027**. With 0 paying customers, multi-tenant auth is YAGNI.

**Don't build:** Auth, OAuth, Stripe Identity, tenant routes. **Don't even think about it** until 1 customer pays.

### Tier 4 — Already shipped (mark as DONE)

| Item | Status | Commit |
|---|---|---|
| PII scrub | ✓ | (earlier) |
| PMTiles | ✓ | 757b14f |
| Status page | ✓ | 757b14f |
| CI | ✓ | earlier |
| Makefile | ✓ | earlier |
| Dockerfile | ✓ | earlier |
| Runbook | ✓ | earlier |
| Disaster Recovery | ✓ | earlier |
| Multi-locale pages | ✓ partial | (es/en/pt/gn 4 keys only) |
| Enrichment pipeline | ✓ | 5c31925 |
| Deploy-meta builder | ✓ | a484672 |
| Webhook ingest | ✓ | earlier |
| 100-role audit | ✓ | earlier |
| Round-2 roast | ✓ | a484672 |

### Tier 5 — What we should NEVER do

(From PLAN_v2 + Round 1 roast):

- ❌ **Real-time scraping** — portals will ban. Batch every 1-3 days.
- ❌ **Mobile native app** — PWA-only. iOS/Android is months.
- ❌ **AI valuation (improve R²)** — currently 0.017. Stop pretending. Hide the widget or remove it.
- ❌ **Multi-cloud deploy** — CF Pages is enough.
- ❌ **Multi-tenancy auth** — until 1 customer pays.
- ❌ **Fancy ML models** — no labeled training data exists.

---

## The order to ship (a 12-week plan)

### Week 1-2 (this week + next): Quick wins
- [ ] **T1.1** Guaraní translations (4 hrs)
- [ ] **T1.2** Lighthouse budget + CI gate (3 hrs)
- [ ] **T1.3** Delete dead files (2 hrs)
- [ ] **T1.4** Wire 4 fetchers into cron (6 hrs)

**Outcome:** O2 90%, O3 75%, +600 listings.

### Week 3-6: Coverage + Stripe
- [ ] **T2.1** Wire argenprop + Clasipar Playwright
- [ ] **T2.2** Cross-source dedupe
- [ ] **T2.3** Stripe-backed API
- [ ] **T2.4** Get to 10K listings

**Outcome:** O1 100%, O5 50%, 10K listings live.

### Week 7-12: Performance + Realtime
- [ ] **T3.1** Mobile Lighthouse 90+
- [ ] **T3.2** Realtime webhook ingest
- [ ] Improve fair-price model (R² → realistic 0.4-0.5 with geographic features) OR **delete it**

**Outcome:** O3 100%, O4 100%, first paying customer.

---

## What you (Ivan) should do this week

If you have **2 hours:**

1. **Hire a Guaraní translator.** $200 to translate the 200 UI strings from Spanish. Don't have me do it — machine-translated Guaraní is gibberish.

If you have **1 day:**

2. **Wire argenprop into the cron.** Run `refresh_properties.sh` manually, verify argenprop listings appear in canonical, deploy. → +20 listings, freshens BCP/INBIO data.

3. **Pick the Stripe tier.** Decide which tier to launch first ($29 GeoJSON or $99 DXF). Update `__STRIPE_CHECKOUT_URL` to a real Stripe Payment Link. Verify the "Buy" button actually opens Stripe Checkout (not disabled).

If you have **1 week:**

4. **Ship the 10K listings.** See Tier 2.4. Either:
   - Asuncion.estate expansion (5,000 → +3,000 = 8,800 listings)
   - All 17 deptos via inmueblespy + argenprop (60 → 1,200 = 7,000 listings)

5. **Cross-source dedupe.** Tier 2.2. Critical for analytics quality.

If you have **1 month:**

6. **Mobile Lighthouse 90+.** Tier 3.1. The single biggest UX improvement.

7. **Stripe-backed API.** Tier 2.3. The single biggest revenue impact.

---

## What you (Erebus) should keep doing

- Daily cron: builds + deploys (already runs)
- Weekly cron: full re-scrape
- Tests stay green (129/131)
- Update `deploy-meta.json` on every commit (now automated)
- Watch for any new "Coming soon" / "TODO" in production HTML
- Surface `runDueDiligence`, `computeInmuebleTax`, `lookupCatastro` in the UI (functions exist, never wired to buttons)

## What you (Erebus) should NOT do without explicit ask

- Don't add more data sources without verifying they ship in production
- Don't add more widgets (current 5 is enough)
- Don't refactor canonicalize_properties.py — Round 1 said it's 573 lines, but it works
- Don't add more doc pages (we have 30+ docs already, 80% are stale)

---

## Key metrics to watch

| Metric | Current | Target (Q3) | Target (Q4) |
|---|---|---|---|
| Listings | 5,844 | 7,000 | 10,000 |
| Sources | 4 | 5 | 6 |
| Tests | 129/131 | 150/155 | 200/210 |
| Lighthouse mobile | n/a | 80 | 90 |
| BCP widget freshness | 24d | 1d | 1d |
| LCP (4G) | 3.2s | 2.0s | 1.5s |
| Bundle size (gzipped) | 327KB | 250KB | 180KB |
| Paid customers | 0 | 0 | 1 |
| Locales complete | 25% (es full, others ~5%) | 75% | 95% |

---

## TL;DR — the 5 things to ship this month

1. **Guaraní translations** (4 hrs, $200 translator)
2. **Lighthouse CI gate** (3 hrs, prevents regression)
3. **Wire 4 fetchers** (6 hrs, freshens data)
4. **Stripe checkout** (1 week, enables monetization)
5. **10K listings via 2 paths** (2 weeks, hits Q3 O1)

After these, the project is **B+** instead of **B-**.

The data is real. The story is good. The codebase works. The gaps are translation, coverage, and money. **Hire a Guaraní translator, wire Stripe, and double the listings. That's the quarter.**
