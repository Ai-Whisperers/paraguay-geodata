# Paraguay Geodata Platform — Improvement Plan

This plan synthesizes 2,500 improvement ideas (50 personas × 50 ideas each) into a structured roadmap.

**Generated:** 2026-07-11
**Status:** Waves 1–4 deployed (P0 + P1 + P2 critical items)

---

## 📊 Brainstorm summary

- **Total ideas:** 2,500
- **Unique work items (after dedup):** ~312
- **Rejected** (out of scope / premature / cargo-cult): ~150

---

## ✅ DEPLOYED (waves 1–4)

### Wave 1 (commit `4f8bd48` + `73bf66d`) — critical bug fixes
- Removed duplicate `LAYER_GROUPS` const
- Fixed `loadINBIOSoja()` orphan call
- Fixed `gbif_species` reference
- Guarded `updateLayerCount` against non-layer IDs
- Fixed `buildGroup` targetLayer signature
- Cache-Control max-age=300 for HTML

### Wave 2 (commit `c12ebfa`) — P0 critical features
- PII scrubbing pipeline (10,898 listings)
- Catastro Nacional WFS integration (4 new layers, 8,238 features)
- Photon geocoder (address search)
- Marker clustering (zoom <11)
- i18n framework (es/en/gn)
- WCAG 2.2 AA (skip-link, focus, contrast, reduced-motion)

### Wave 3 (commit `8d7db03`) — P1 features
- Market signals (auto-computed from properties)
- Share view + embed widget + geolocation
- URL hash sync (?lat=&lon=&z=&layers=)
- PWA manifest (installable)
- Price history tracking tool

### Wave 4 (commit `2a82ea2`) — P2 ML
- Fair-price ML model (10,840 samples, 14 per-depto regressions)
- Fair-price badges on every property popup
- Yield calculator (gross/net yield, payback)

---

## 🚧 Roadmap (remaining work items)

### Phase 5 — Data freshness & automation (1-3 months)
- **F1**: Auto-refresh scrapers (cron job) — Infocasas, TuLugar, Clasipar
- **F2**: Auto-merge new data into `properties_latest.geojson`
- **F3**: Auto-retrain fair-price model (weekly)
- **F4**: Data freshness SLO + alerting (any layer >7d stale)
- **F5**: Dedupe pipeline (cross-source via image pHash + agent hash)

### Phase 6 — Domain tools (3-6 months)
- **D1**: Yield-by-barrio choropleth
- **D2**: Rent-vs-sale ratio heatmap (per barrio)
- **D3**: Days-on-market estimator
- **D4**: Comparable-properties tool ("show me similar listings")
- **D5**: Investment heatmap (yield × price × area)
- **D6**: Climate risk layer (NASA climate projections)
- **D7**: Indigenous territory overlay (INDI)
- **D8**: Flood-risk overlay (HydroSHEDS + JRC Global Flood Awareness)
- **D9**: Deforestation alerts (Hansen + monthly GLAD)

### Phase 7 — Institutional sustainability (6-12 months)
- **I1**: Partner with university (UNA, UCA, UP) for institutional host
- **I2**: Apply for IDB Lab / World Bank / Open Data Institute grants
- **I3**: Government MOU with Catastro Nacional (formal data feed)
- **I4**: License + governance docs (CC-BY 4.0 for data, MIT for code)
- **I5**: Multi-language moderation (en/es/gn)
- **I6**: Contributor agreement + code of conduct
- **I7**: Disaster recovery (R2 backups weekly)

### Phase 8 — Advanced features (12+ months)
- **A1**: Mobile app shell (Capacitor → Android/iOS)
- **A2**: WebSocket live updates (new listings within 30s)
- **A3**: User accounts + saved searches
- **A4**: OAuth login (Google + GitHub)
- **A5**: Paid premium tier (agent analytics, custom exports)
- **A6**: API keys + rate limiting
- **A7**: Webhook subscriptions
- **A8**: Vector tiles (MVT) for OSM roads (5.6 MB → 200 KB)
- **A9**: PostGIS backend (replace static GeoJSON files)
- **A10**: 3D terrain (Cesium for Chaco landscape)

---

## 🚫 Rejected ideas (with reasoning)

### Out-of-scope (different project)
- ❌ B2B SaaS pricing tiers — this is open civic data, not a SaaS
- ❌ Series A pitch deck — institutional funding (grants) is the path
- ❌ Mobile app (native) — PWA is more appropriate; $50K+/yr to maintain
- ❌ Stripe Connect / PIX for listings — listings are scraped public data
- ❌ HIPAA-grade health analytics — impossible without consent

### Premature
- ❌ Most "ML/AI" ideas — need 100K+ listings before ML adds value
- ❌ Custom 3D terrain — Cesium adds 2MB JS; not worth the perf hit at current scale
- ❌ Twitter/X content calendar — no social presence to amplify
- ❌ YouTube channel / podcast series — unclear audience

### Generic SaaS advice (cargo cult)
- ❌ "Improve developer experience" — we don't have a developer ecosystem yet
- ❌ "Build an SLA dashboard" — single-server project, SRE overkill
- ❌ "Investor reporting" — same; no investors
- ❌ "Negotiate vendor contracts" — single-vendor (Cloudflare)
- ❌ "Quarterly OKRs" — solo/small-team project, agile not needed

---

## 🎯 Top 10 highest-impact ideas (if forced to pick)

1. **Auto-refresh scrapers** (F1) — current data is stale after a few weeks
2. **PostGIS migration** (A9) — 100× query speed for filters
3. **Vector tiles** (A8) — 30× smaller initial payload
4. **User accounts + saved searches** (A3) — repeat-visit value
5. **Institutional partner** (I1) — sustainability
6. **Indigenous territory overlay** (D7) — legal/ethical requirement
7. **Climate risk layer** (D6) — Paraguay's #1 long-term risk
8. **Mobile-first redesign** — currently desktop-first
9. **OAuth + API keys** (A4) — enables B2B
10. **Catastro National WFS live feed** (I3) — replaces our manual scraping

---

## 📚 References

- **Catastro Nacional WFS:** https://www.catastro.gov.py/geoserver/wfs
- **GBIF API:** https://www.gbif.org/developer/summary
- **Photon geocoder:** https://photon.komoot.io
- **Open-Meteo (free weather):** https://api.open-meteo.com
- **NASA POWER:** https://power.larc.nasa.gov
- **INBIO Paraguay:** https://inbio.org.py
- **BCP:** https://www.bcp.gov.py
- **Geofabrik PY OSM:** https://download.geofabrik.de/south-america/paraguay.html