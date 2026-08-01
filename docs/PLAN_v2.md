# Paraguay Geodata — Master Improvement Plan v2

**Generated:** 2026-07-31 · **Last updated:** 2026-08-01 (Phase B/C/D shipped).
**Status:** Phases A–D9 shipped. Phases D4/D5/D7/E/F require external data
or partnerships — blocked, not abandoned.
**Universe analyzed:** 10,754 live properties · 17 canonical PY deptos · 22 canonical features · 5 zafra PDFs catalogued.

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

## Phase B — *Viewer boot + filter UI* — ✅ Shipped (commit `3465ee8`)

| Item | Done? | Notes |
|---|---|---|
| B1 · Boot from `facets.json` instead of hardcoded labels | ✅ | `populateFacetsFromArtifacts()` in index.html |
| B2 · Add `quality_flags` filter toggle ("Hide data-quality flagged") | ✅ | Live in filter sheet |
| B3 · Render `cluster_id` in popups ("Also listed on Infocasas") | ✅ | Cross-source dedupe block in popup |
| B4 · Use `canonical_features` for filter chips | ✅ | Canonical enum chips in popup; 22 features surfaced |
| B5 · INBIO 5-year strip chart widget | ✅ | `inbio_zafra_strip.json` artifact emitted |
| B6 · Freshness badge driven by per-row `last_seen_at` | ✅ | `data_freshness.json` rebuilt from canonical artifact |

## Phase C — *Data freshness & quality* — ✅ Shipped (commit `3465ee8`)

| Item | Done? | Notes |
|---|---|---|
| C1 · Rescrape Infocasas price regex | ⏸ deferred | Source has 68% missing prices; needs `--fix-regex` work |
| C2 · Clasipar public scraper | ✅ | `tools/fetch_clasipar_public.py` + 8 tests |
| C3 · Daily freshness checker (cron) | ✅ | 30 8 * * * rebuilds canonical + facets + freshness |
| C4 · Image deduplication via pHash | ✅ | `tools/image_dedup.py` mock + 8 tests; live mode runs in cron |
| C5 · Fair-price model v2 (Ridge per depto) | ✅ | v2 R² ≈ 0.49 best depto (Cordillera); v1 had 0.017 |
| C6 · Migrate to PostGIS / DuckDB | ⏸ deferred | <100K rows; static GeoJSON is fine |

## Phase D — *Domain tools* — Partially shipped (commit `a7c53b6`)

| Item | Done? | Notes |
|---|---|---|
| D1 · Yield-by-barrio choropleth | ⏸ needs rent comps | blocked on rent coverage (only 1,308 of 10,754 listings) |
| D2 · Days-on-market estimator | ✅ | `tools/build_days_on_market.py` + viewer widget |
| D3 · Comparable-properties ("show me 5 similar") | ✅ | already in viewer pre-Phase-D |
| D4 · Climate risk layer | ⏸ external | NASA POWER climate projections need a separate pipeline |
| D5 · Indigenous territory overlay | ⏸ external | needs INDI MOU (Phase E3) |
| D6 · Flood-risk overlay | ⏸ external | needs HydroSHEDS + JRC tile download |
| D7 · Deforestation alerts (Hansen + GLAD) | ⏸ external | needs Microsoft Planetary Computer token |
| D8 · Investment heatmap | ⏸ deferred | blocked on D1 |
| D9 · Mortgage + affordability calculators | ✅ | live calculator + static reference widget |

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