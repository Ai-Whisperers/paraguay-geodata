# Paraguay Geodata — Documentation Index

Map of every doc in this repo. Read order for a new agent:

1. `README.md` — one-page project summary
2. `STATUS.md` — live state + blockers
3. `docs/INDEX.md` (this file)
4. `ARCHITECTURE.md` — design
5. `CLAUDE.md` — agent ops
6. The doc matching your task (`docs/sources/`, `docs/operations/`, etc.)

## Root

| File | Purpose |
|---|---|
| `README.md` | One-page summary for humans; canonical URL/quickstart |
| `ARCHITECTURE.md` | Design — pipeline, storage layout, north-star principles |
| `CLAUDE.md` | Instructions for AI agents reading/writing this repo |
| `STATUS.md` | Live state — phase tracker, open work, decisions made |
| `PROVENANCE.md` | Source data licensing + attribution (TBD Phase 1) |
| `CREDITS.md` | Humans + tools + upstream providers |
| `LICENSE` | MIT (code), CC0 (data) |

## docs/sources/

| File | Purpose | Status |
|---|---|---|
| `satellite.md` | Satellite imagery + DEM data sources (ranked, auth, licences) | ✅ |
| `cadastre.md` | Public padrones + operator-supplied escritura anchors | ✅ |
| `listings.md` | Real-estate portals (infocasas, propiedades.com.py, baiker) | ⏳ (Phase 2 — see `docs/operations/properties-pipeline.md` for now) |
| `prices.md` | Public appraisal + indicador del m² construction costs | ⏳ (Phase 2 — see `docs/operations/price-model.md` for now) |
| `biodiversity.md` | GBIF, MapBiomas Chaco, FIRMS, Hansen GFC, SoilGrids | ⏳ (fold into `satellite.md` + `environment.md`) |
| `administrative.md` | INE — departamentos/distritos/barrios/manzanas + locales (salud/policial/educación) | ✅ |
| `businesses.md` | DNCP tenders, MIC maquila, SET/RUC, IPS, BCP — commercial activity | ✅ |
| `agriculture.md` | INBIO, INFONA, SENAVE, SENACSA, SoilGrids, Guyra Paraguay | ✅ |
| `infrastructure.md` | ANDE power, ESSAP water, MOPC roads, COPACO fiber, mobile coverage | ✅ |
| `environment.md` | DINAC weather, MADES air quality, FIRMS fires, CHIRPS rainfall, JRC floods | ✅ |
| `socioeconomic.md` | INE EPH + IPM + CNPV, BCP macro, Policia Nacional crime, AHK/UIP investment | ✅ |

## docs/operations/

| File | Purpose | Status |
|---|---|---|
| `national-tile-fabric.md` | Phased rollout: tile fabric, phase exit criteria, risk register | ✅ |
| `properties-pipeline.md` | Listings scrape + dedup + cross-ref + deploy | ✅ |
| `price-model.md` | Hedonic kriging → $/ha raster per departamento | ✅ |
| `data-inventory.md` | **Master catalog** — every layer the map can show, with phase assignment | ✅ |
| `api-key-checklist.md` | API key registration table for all upstream data providers (TBD Phase 1) | ⏳ |

## docs/ethics/

| File | Purpose | Status |
|---|---|---|
| `scraper-policy.md` | Ethical gate — when to scrape, when to stop, PII strip table | ✅ Phase 0 |

## docs/specs/

| File | Purpose | Status |
|---|---|---|
| `listing-schema.json` | Listings GeoJSON schema (Phase 2) | ⏳ |
| `tile-metadata-schema.json` | Per-tile metadata.json schema (Phase 1) | ⏳ |
| `price-surface-schema.json` | Public surface GeoJSON schema (Phase 2) | ⏳ |

## docs/reference/

| File | Purpose | Status |
|---|---|---|
| `lqv-lineage.md` | Lineage notes: which LQV scripts we inherit + what's adapted | ⏳ Phase 1 |
| `upstream-api-cheatsheets/` | Per-API quick-reference (Copernicus, Esri, MapBiomas, etc.) | ⏳ Phase 1 |

## When this file gets stale

When you add a new doc under any `docs/<category>/` directory, add a row to the relevant table above. Update in the SAME commit as the new doc.
