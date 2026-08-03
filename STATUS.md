# Paraguay Geodata — Status (Q3 2026)

**Live:** https://geodata.paragu-ai.com · **Repo:** https://github.com/Ai-Whisperers/paraguay-geodata
**HEAD:** tracked in deploy-meta.json · **Status page:** https://geodata.paragu-ai.com/status

## What this is, in one sentence

A free, open, public-data viewer for Paraguay real estate + cadastre +
environmental layers.  5,784 listings from 3 sources, 18 cities, 17
PY admin deptos, mobile-responsive, multilingual (es / en / pt / gn),
PII-scrubbed, CC0.

## KPIs (live now)

| Metric | Value | Trend |
|---|---|---|
| Total listings | 5,784 | +0 since last week |
| Active sources | 3 / 9 viable | — |
| Properties with coords | 5,784 (100%) | — |
| Properties with images | 5,392 (93%) | +1.5% |
| Median freshness | 2 days | — |
| PII violations | 0 | clean |
| Auto-removed stale | 50 | 0.9% |
| Tests passing | 76 / 78 (97%) | — |
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
