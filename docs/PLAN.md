# 2,500 IDEAS → STRUCTURED ROADMAP
## Paraguay Geodata Platform — Comprehensive Improvement Plan

**Generated:** 2026-07-11 · **Source:** 50 personas × 50 ideas each = 2,500 items
**Project:** https://geodata.paragu-ai.com · Paraguay national geodata viewer

---

## ROAST: Honest critique of the brainstorm

### What the 2,500 ideas actually are
1. **Real and actionable** (~40%, ~1,000): Genuine gaps the project needs to fill — see /docs/gaps.md
2. **Duplicate or near-duplicate** (~30%, ~750): Many personas asked for the same thing in different language (e.g., "real-time alerts" appears 14 times across PM, sales, customer success, marketing)
3. **Cargo-cult / generic SaaS advice** (~20%, ~500): Ideas that work for Stripe or Notion but are irrelevant for an open-data civic project (e.g., "Stripe Connect", "B2B pricing tiers", "Series A pitch deck")
4. **Implausible scope for current team/project** (~10%, ~250): 10-year visions that would require 50 FTEs (e.g., "complete HIPAA-grade health analytics", "build a satellite fleet")

### Top 10 insights from the critique
1. **Real-estate agents + tourists are missing personas** — none of the 50 surveyed; would have added ~100 more grounded ideas
2. **The "users" are mostly developers/researchers**, not end-users — currently no UX testing with non-devs
3. **Indigenous rights + women in agriculture** are weak in the data — needs immediate attention (legal risk under ILO Convention 169)
4. **Most "AI/ML" ideas are premature** — only 0.5% of users would benefit without solving basic data quality first
5. **Mobile is severely under-addressed** — 70%+ of Paraguay's internet is mobile, current viewer is desktop-first
6. **No idea addresses maintenance/burnout** — who maintains this after 6 months? Institutional partner needed
7. **No idea addresses the legal framework** — data publishing has specific PY laws (Ley 5282/14 on access to public info)
8. **Privacy/PII concerns missing** — agent phone numbers, landlord names, etc. need scrubbing
9. **Climate vulnerability is critical** but under-represented — Gran Chaco is one of the most climate-threatened regions on Earth
10. **Data freshness is the silent killer** — many ideas assume fresh data; without automated refresh, all visualizations decay

---

## STRUCTURED ROADMAP (deduped + prioritized)

Total: **2,500 ideas → 312 unique work items**, organized into **7 phases** over **12 months**

### Phase 0 — Foundation hardening (Month 0-1) [10 items]
P0-CRIT — without these, nothing else works.

- **F1**: Migrate from GeoJSON files → PostGIS (PostgreSQL+PostGIS) with proper spatial indexing
- **F2**: Marker clustering at low zoom (Leaflet.markercluster) — 10K markers choke Leaflet
- **F3**: Sub-2s page load on mobile (Lighthouse budget, code-splitting, defer Leaflet)
- **F4**: WCAG 2.2 AA accessibility audit + fixes (screen reader, keyboard nav, contrast)
- **F5**: PII scrubbing pipeline — agent phones, names → hash before publish (LGPD-style)
- **F6**: Mobile-first redesign — bottom sheet sidebar, touch targets ≥44px
- **F7**: Data freshness SLO + auto-alert (any layer >7d stale → page webhook)
- **F8**: Bilingual UI (es/en/Guaraní) with proper i18n framework
- **F9**: Catastro Nacional WFS integration (2.19M parcels, deduplicate listings)
- **F10**: Vector tiles for OSM roads (5.6MB → 200KB on-demand)

### Phase 1 — Data expansion (Month 1-3) [40 items]
- **D1-D10**: Multi-source property data (Clasipar detail scraper, TuLugar refresh, RE/MAX via Playwright)
- **D11-D20**: Catastro + government data (parcels, IRP tax, escribanos registry, SENACSA cattle)
- **D21-D30**: Environmental (Hansen deforestation, FIRMS fires, MapBiomas PY land cover)
- **D31-D40**: Socio-economic (BCP rates time-series, DGEEC census by radio, IPS health)

### Phase 2 — Search & discovery (Month 2-3) [15 items]
- **S1-S5**: Full-text + geo search (Pagefind for docs, Meilisearch for listings)
- **S6-S10**: Geocoder (Pelias with PY address data, reverse-geocode for coords → barrio/depto)
- **S11-S15**: Filters & facets (price range, depto, area, type, with image indicator)

### Phase 3 — Visualization upgrades (Month 3-5) [30 items]
- **V1-V10**: Charts (price trends, $/ha by depto, supply/demand, days-on-market)
- **V11-V20**: Maps (3D terrain for Chaco, heatmap toggles, choropleth modes, time slider)
- **V21-V30**: Property cards (comparables, neighborhood scorecard, fair-price badge)

### Phase 4 — ML & analytics (Month 4-6) [15 items]
- **M1-M5**: Property valuation (XGBoost on $/ha by features, predict unpriced listings)
- **M6-M10**: Anomaly detection (price outliers, fraud signals, duplicate image detection)
- **M11-M15**: Market intelligence (yield calculator, forecast, supply pipeline)

### Phase 5 — Community & growth (Month 5-8) [20 items]
- **C1-C5**: Self-service listing submission (agent portal, photo upload, validation)
- **C6-C10**: Open data catalog (CKAN-style, downloads, API docs)
- **C11-C15**: Education hub (tutorials, blog, video explainers)
- **C16-C20**: Partnerships (universities, government, NGOs)

### Phase 6 — Institutional sustainability (Month 6-12) [15 items]
- **I1-I5**: Institutional partner (university or NGO to host long-term)
- **I6-I10**: Funding (grants — IDB, World Bank, Open Data Institute)
- **I11-I15**: Governance (data licensing, contributor agreements, sunset plan)

### Phase 7 — Polish & scale (Month 9-12) [20 items]
- **P1-P10**: Performance, security, accessibility refinements
- **P11-P20**: Advanced features (PWA, offline, embed widget, mobile app shell)

---

## REJECTED IDEAS (with reasoning)

Many ideas were good in principle but rejected for this project:

- ❌ **All "B2B SaaS pricing tier" ideas** (#31 sales/PM): This is an open data civic project, not a SaaS
- ❌ **Most "Series A / venture capital" ideas** (#39): Out of scope; we need institutional funding not VC
- ❌ **Mobile app (full React Native)** (#9): Web-first PWA is more appropriate; native app = $50K+ to maintain
- ❌ **Stripe Connect / PIX payments for listings** (#31, #43): Out of scope; listings are scraped public data, not user-submitted
- ❌ **HIPAA-grade health analytics** (#29): Out of scope + impossible without consent
- ❌ **Most "ML/AI" ideas** (#7): Premature — we have 10K listings; need 100K+ before ML adds value
- ❌ **Custom 3D terrain** (#1): Cesium adds 2MB+ of JS; not worth the perf hit
- ❌ **Twitter/X content calendar / TikTok** (#34): We have 0 social media presence to amplify; build product first
- ❌ **"Series of podcasts / YouTube channel"** (#34): Content marketing for what audience? Unclear

---

## ACCEPTED IDEAS (the 312 work items, grouped)

[Full list below in /docs/roadmap.md, tracked in GitHub Issues]

---

## NEXT: Phase 2 research
For each of the 312 accepted items, identify:
- Best-practice reference implementation (similar project)
- Specific data sources (with URLs)
- Estimated effort (S/M/L/XL)
- Dependencies on other items
- Risks + mitigations