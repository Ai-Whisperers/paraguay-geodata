# Cadastral & Property — Data Sources

## 1. Servicio Nacional de Catastro (SNC) — Paraguay

| Field | Value |
|---|---|
| URL | https://www.catastro.gov.py/ |
| Auth | None (browse-first) |
| Format | Web portal + consulta padronales |
| License | Public records (datos públicos) |
| Refresh cadence | Continuous (operator-issued) |
| Confidence | HIGH for: district lookup; LOW for: programmatic scraping (per `paraguay-open-data-fetch` vendor pitfall) |

**What we extract**:
- Padron number lookup (cuenta corriente catastral)
- District-level GIS overlays (where available via portal map)
- Titulo antecedentes (escritura history)

**Pitfall**: SNC is browse-first. Per the `paraguay-open-data-fetch` skill: "Programmatic access is unstable; the portal is browse-first, with periodic 503s. Padrones are issued by district, not by lat/lon. Use the operator's Anexo I (escritura bundle) as the authoritative source. Treat the public index as a discovery surface, not a parser target."

**Our approach**:
- Treat SNC as **discovery surface** — give the user a "look up padron on SNC" link in the listing popup
- Cross-reference our listings/escrituras against SNC district codes
- Provide a "How to file an informe catastral" instructions page, not a scraper

## 2. Operator-Supplied Escritura Anchors

| Field | Value |
|---|---|
| Source | Operator-supplied via Anexo I / Notaría bundles |
| Format | CSV (lat, lon, price_pyg, price_usd, area_ha, district, fuente) |
| License | Private (PII adjacent — owner names) |
| Refresh cadence | Per deal |
| Confidence | HIGHEST (notary-stamped transactions) |

**What we extract**:
- (lat, lon, $/ha) tuples → kriging anchors for the price surface
- District cross-validation against our listings
- Quality control: listings with price >2× or <½ nearest escritura $/ha get flagged

**Pipeline**:
1. Operator drops CSV in `data/cadastre/escrituras/<date>_anchor_set.csv`
2. `scripts/match_escrituras.py` runs nightly, matches listings within 200m
3. Each listing gets `escritura_anchor_id`, `escritura_distance_m`, `price_band_vs_anchors`

## 3. Public Notary Data (Escribanía)

| Field | Value |
|---|---|
| URL | Notaría portal (varies) |
| Auth | Per-notaría |
| Format | PDF / notaría-specific |
| Confidence | HIGH for individual transactions |

We don't scrape this — it would require subscribing to 50+ notaría portals. Instead: operator-supplied anchors + best-effort listings cross-ref.

## What we DO NOT ship

- Owner PII (names, RUC, CI)
- Specific padron numbers with debtor flags (legal liability)
- Anything behind authentication

## See also

- `docs/operations/properties-pipeline.md` — listings scraping, ethics gate
- `docs/operations/price-model.md` — escritura anchors → kriging
- `docs/specs/listing-schema.json` — listings GeoJSON schema (Phase 2 deliverable)