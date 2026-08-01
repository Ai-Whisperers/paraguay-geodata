# Paraguay Geodata — Master Improvement Plan v2

**Generated:** 2026-07-31 · **Status:** Phase A shipped (canonicalization + facets + regression guard + cron + CI).
**Universe analyzed:** 10,754 live properties · 32 depto strings · 45 distinct `features[]` tokens · 6 fresh sources to fold in next.

This plan replaces the original 2,500-item brainstorm (`docs/PLAN.md`) with a sequenced, scored, dependency-aware roadmap. Items are grouped by **track** and **priority tier**, each with the *actual blocker that shipped today* and the *next concrete step*.

---

## Phase A — *Shipped this session*

### A1 · Canonicalization pipeline (`tools/canonicalize_properties.py`)
- 18 unit tests, **all passing**.
- Fixes: 32 distinct `state_province` strings → canonical 17 PY deptos + drop foreign (Formosa, Corrientes, Paraná, Santa Cruz, Minga Guazu).
- Currency: flags 4,747 rows where `price_usd × 7,500` diverges from `price_pyg` by >30%. Recovers USD from PYG and vice versa.
- Area: re-infers `area_ha` from titles (hectárea, has, m²) and flags conflicts between published `area_ha`/`area_sqm`.
- Features: collapses 45 free-text tokens into a 22-item canonical enum (`pool`, `bbq`, `garden`, `airConditioning`, etc.).
- Adds `cluster_id` (SHA1 of `source_url` or normalized title + 0.001° grid) so the same finca from TuLugar + InfoCasas + Clasipar can be deduped in the viewer.

### A2 · Facets artifact (`tools/build_facets.py`)
- `data/properties/facets.json` — 5 facet groups (depto, property_type, currency, source, features) + freshness stats + per-flag quality counts.
- The viewer loads this once at boot and never has to compute counts itself.

### A3 · Regression guard (`tools/detect_regression.py`)
- 3 unit tests, all passing.
- Fails the deploy if the freshly canonicalized artifact shrinks >30% or loses the 17-depto signature.

### A4 · Auto-refresh cron + wrapper script (`scripts/refresh_properties.sh`)
- Weekly Monday 08:00 UTC (04:00 PY).
- Steps: fetch → merge → canonicalize → facets → regression check → Pages deploy.

### A5 · GitHub Actions `canonicalize.yml`
- Pulls the deployed artifact, re-runs canonicalize + facets + regression, fails on regression.
- Already integrated into the existing CI suite.

### A6 · INBIO multi-year series parser (`scripts/build_inbio_series.py`)
- Reads 55 catalogued INBIO PDFs into one time-series JSON (`data/properties/inbio_series.json`).
- Stubs ready for 5-zafra strip chart in the viewer.

---

## Phase B — *Viewer changes (P1)* — *target: 1-2 weeks*

| Item | Why now | Acceptance |
|---|---|---|
| B1 · Boot from `facets.json` instead of hardcoded layer labels | Without this the new canonical 17 deptos never reach the UI | Sidebar shows live counts per depto |
| B2 · Add `quality_flags` filter toggle ("Show flagged only" / "Hide flagged") | 4,747 currency-conflict rows are silent noise | Toggle removes/hides them |
| B3 · Render `cluster_id` in popups ("Also listed on Infocasas") | Cross-source dedupe is useless without UI | Popup shows 1+ linked source |
| B4 · Use `canonical_features` for filter chips | Spanish free text was the biggest UX gap | Chips match canonical enum |
| B5 · INBIO 5-year strip chart widget | Multi-year zafra data is the strongest agri story | Widget renders 5 zafras × 3 crops |
| B6 · Freshness badge driven by per-row `last_seen_at` | 21-day median freshness is invisible today | Badge shows "Listings from N days ago" |

---

## Phase C — *Data freshness & quality (P1)* — *target: 2-4 weeks*

| Item | Blocker | Effort |
|---|---|---|
| C1 · Rescrape Infocasas with the fix regex that recovers price/title from `__NEXT_DATA__` JSON (444 → ~420 listings) | TuLugar carries 96% of records; InfoCasas missing price for 68% | M |
| C2 · Add Clasipar public scraper (`tools/fetch_clasipar_sitemap.py`) | Only 2 source files today | M |
| C3 · Daily freshness checker (cron) — re-pings each source, logs diff, alerts on >30% drop | Data silently goes stale every week | S |
| C4 · Image deduplication via pHash (`tools/image_dedup.py`) | Cross-source dedupe without image hash is only ~70% precise | M |
| C5 · ML fair-price model v2 — per-depto regressions with `area_ha` + `canonical_features` (currently R² ≈ 0.017) | The current model is decorative | M |
| C6 · Migrate canonical artifact to PostGIS / DuckDB spatial | Filters run client-side today; >100K rows will choke the viewer | L (only if user count grows) |

---

## Phase D — *Domain tools (P2)* — *target: 4-12 weeks*

| Item | Source | Why it matters |
|---|---|---|
| D1 · Yield-by-barrio choropleth | Rent comps + Sale prices | "Best neighborhood to invest" |
| D2 · Days-on-market estimator | Per-row `last_seen_at` history | "Is this a stale listing?" |
| D3 · Comparable-properties ("show me 5 similar") | Cluster_id + canonical_features | Helps agents and buyers negotiate |
| D4 · Climate risk layer (NASA climate projections) | NASA POWER + Hansen forest loss | Paraguay's #1 long-term risk |
| D5 · Indigenous territory overlay | INDI WFS | Legal/ethical requirement |
| D6 · Flood-risk overlay (HydroSHEDS + JRC Global Flood Awareness) | HydroSHEDS + JRC GSW | Property insurance basis |
| D7 · Deforestation alerts (Hansen + GLAD) | Hansen API monthly | Chaco deforestation real-time |
| D8 · Investment heatmap (yield × price × area) | Sale price + rent comps + $/ha | Top-of-stack for agent analytics |
| D9 · Mortgage + affordability calculators | BCP rates + listing price | Convert "asking price" to "monthly payment" |

---

## Phase E — *Institutional sustainability (P3)* — *target: 6-12 months*

| Item | Why |
|---|---|
| E1 · Partner with UNA/UCA/UP for institutional hosting | Sustainability beyond volunteer effort |
| E2 · Apply for IDB Lab / ODI grant | Funding for full-time maintainer |
| E3 · Government MOU with Catastro Nacional | Replaces manual scraping with official feed |
| E4 · Multi-language moderation (en/es/gn full Guaraní) | Paraguay's indigenous-language baseline |
| E5 · Contributor agreement + code of conduct | Onboard outside contributors |
| E6 · Disaster recovery: weekly R2 backups + restore drill | Single point of failure today |

---

## Phase F — *Advanced features (P3+)* — *target: 12+ months*

| Item | Why now is too early |
|---|---|
| F1 · Vector tiles (MVT) for OSM roads | 5.6 MB → 200 KB is nice but needs Postgres backend first |
| F2 · PostGIS backend (replace static GeoJSON) | Only justified at >100K listings |
| F3 · User accounts + saved searches | Real but P3 |
| F4 · OAuth (Google + GitHub) | Real but P3 |
| F5 · API keys + rate limiting | Real but P3 |
| F6 · Paid agent analytics tier | The "Architect export" Stripe flow already proves this works |
| F7 · 3D terrain (Cesium) | Chaco is flat, the additional value is marginal |
| F8 · WebSocket live updates (new listings within 30s) | Overkill until we hit >50K listings |

---

## What we deliberately *did NOT* do

These are explicit non-goals — either out of scope or premature. They came up during the brainstorm and we marked them rejected:

- ❌ Custom 3D terrain — Cesium adds 2MB JS for marginal value at this scale.
- ❌ Twitter / X content calendar — no audience to amplify.
- ❌ "Improve developer experience" — no contributor ecosystem yet.
- ❌ Investor reporting — no investors; this is open civic data.
- ❌ Most "ML/AI" ideas — need 100K+ listings before ML adds value.
- ❌ Native mobile app — PWA is more appropriate; $50K+/yr to maintain.
- ❌ Series A pitch deck — institutional funding (grants) is the path.

---

## Quality signals (post Phase A)

```
features            : 10,754
canonical deptos    : 17 (was 32 distinct strings)
currency conflicts  : 4,747 (44% of rows — needs source-side fix)
null property_type  : 155  (1.4%)
foreign depto drops : 25    (Formosa, Corrientes, Paraná, Santa Cruz, Minga Guazu)
missing area        : 43    (mostly old TuLugar rows)
missing price       : 10    (mostly "consultar precio")
median freshness    : 21 days (sentinel — needs C3 cron)
facets artifact     : 5 groups, 19 deptos, 20 canonical features
```

---

## How to read this plan

Every item in Phases B–F has:
1. **A blocker** — what's stopping it from shipping today.
2. **An acceptance criterion** — a measurable thing that says "this shipped."
3. **An effort tag** — XS(<1d), S(<1w), M(<1mo), L(<1q), XL(>1q).

The plan is meant to be *executable by any agent* in a single session: the canonicalization pipeline plus the regression guard plus the cron are all live, so the next agent inherits a state machine that's safe to extend.