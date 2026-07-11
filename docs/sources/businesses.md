# Businesses & Commercial Activity — Data Sources

The map should show not just **what's on sale** (listings) but **what's already there** (active businesses) and **what's being built** (public tenders). This is what turns a real-estate viewer into a **commercial intelligence platform**.

## 1. DNCP — Dirección Nacional de Contrataciones Públicas (PUBLIC TENDERS)

| Field | Value |
|---|---|
| URL | https://www.contrataciones.gov.py/ |
| API | https://www.contrataciones.gov.py/datos/data (V3 — V1/V2 deprecated) |
| Auth | **Free API key** (register at datos.contrataciones.gov.py — see portal) |
| License | Public info |
| Format | JSON / OCDS (Open Contracting Data Standard) |
| Refresh | Daily |

### What we extract

| Data | Use |
|---|---|
| **Llamados** (tender calls) | Public works being planned — road construction, school builds, hospital expansions |
| **Adjudicaciones** (awards) | Who won, for how much, in which district |
| **Contratos** (contracts) | Active projects with timelines |
| **Proveedores** (suppliers) | Companies winning public business |
| **DNCP Catalog 2024-2025** | ~10,000-15,000 active calls/year, ~$3-4B total |

### Map overlay design

- **By call**: bubble on the project lat/lon, size = $ amount, color = call status (open/closed/adjudicated)
- **By company**: heatmap of where each contractor works
- **By category**: construction, healthcare supplies, IT services, vehicles
- **Time scrubber**: view past 12 months, predict next 6 months

### Implementation plan

| Tool | What it does |
|---|---|
| `tools/fetch_dncp.py` | Paginated fetch from V3 API → `data/dncp/calls_<date>.geojson` |
| `tools/fetch_dncp_awards.py` | Fetch adjudicaciones → `data/dncp/awards_<date>.geojson` |
| `tools/fetch_dncp_suppliers.py` | Fetch proveedores → `data/dncp/suppliers.csv` (deduped) |
| `tools/build_dncp_heatmap.py` | Per-distrito aggregate: contracts/mo, $/contract |

### Operator workflow

1. Apply for API key at https://www.contrataciones.gov.py/datos/data
2. Drop key into `.env` (mode 0600)
3. Cron `paraguay-geodata-fetch-dncp` runs daily
4. Viewer: click any bubble → see tender detail (entity, amount, timeline)

## 2. MIC — Ministerio de Industria y Comercio

| Field | Value |
|---|---|
| URL | https://www.mic.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

- **Maquila registry** — textile/garment factories (a major PY export sector)
- **Industry census** — companies by district, sector, size
- **Import/export statistics** — customs data per aduana

### Implementation plan

| Tool | What it does |
|---|---|
| `tools/fetch_mic_maquila.py` | Scrape maquila registry → GeoJSON |
| `tools/fetch_mic_companies.py` | Pull industry census → `data/mic/companies_<date>.geojson` |
| `tools/build_industry_heatmap.py` | Employment density per district |

## 3. SET — Subsecretaría de Estado de Tributación (TAX ROLL)

| Field | Value |
|---|---|
| URL | https://www.set.gov.py/ |
| Auth | **RUC lookup is public** for individuals/businesses |
| License | Public info |

### What we extract

- **RUC validation** — when a listing claims a "real estate agency," validate the RUC
- **Active taxpayers** by district (rough proxy for formal economic activity)
- **Tax regime breakdown** (Simplificado, General, etc.)

### API

- RUC lookup: `https://www.set.gov.py/portal/PARAGUAY-SET-405` (form-based; not stable for scraping)
- **Use case**: only RUC validation, not mass scrapes

### Implementation plan

| Tool | What it does |
|---|---|
| `tools/ruc_lookup.py` | Single-RUC validation |
| `scripts/validate_listings_ruc.py` | Bulk validate listing agencies |

## 4. IPS — Instituto de Previsión Social

| Field | Value |
|---|---|
| URL | https://www.ips.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

- Active employer registry (companies with formal employees)
- Health facility locations (already in INE)

**Use**: validate company activity, rough employment density.

## 5. BCP — Banco Central del Paraguay

| Field | Value |
|---|---|
| URL | https://www.bcp.gov.py/ |
| Auth | None |
| Format | Excel / CSV |

### What we extract

- Monthly macroeconomic indicators (FX rates, inflation, deposits)
- Banking penetration by district (banks + ATMs + financial cooperatives)

**Use**: validate the `price_pyg` → `price_usd` conversion + financial inclusion overlay.

## 6. INBIO — Instituto de Biotecnología Agrícola (AGRICULTURE BY SATELLITE)

| Field | Value |
|---|---|
| URL | https://inbio.org.py/ |
| Auth | None for public reports |
| Format | PDF reports + GeoTIFF supplements |
| License | Public info (with attribution) |

### What we extract

| Data | Periodicity | Use |
|---|---|---|
| **Superficies de siembra** (crop area by season) | Per zafra (Sep-Jun) | Agricultural intensity overlay |
| **Soja yield per department** | Per zafra | Productivity heatmap |
| **Maíz, trigo, girasol, sésamo, arroz** | Per zafra | Crop diversity overlay |
| **Cobertura nativa vs cultivada** | Per year | Deforestation overlay (validated) |

### Implementation plan

| Tool | What it does |
|---|---|
| `tools/fetch_inbio.py` | Scrape zafra reports → GeoTIFF + CSV |
| `tools/build_agro_intensity.py` | Crop area + yield per district |

## 7. Clasipar / MercadoLibre PY / Vinted PY — Private Listings

Already covered in `properties-pipeline.md` (separate from formal commercial registries).

## What we DO NOT integrate

- Per-individual commercial transactions (bank secrecy)
- Notary-level ownership history (PII)
- Tax filings detail beyond RUC validation
- Wholesale prices by company (commercial sensitivity)

## Map overlay design (commercial)

```
┌──────────────────────────────────────────────┐
│ COMMERCIAL LAYERS (toggleable)                │
│                                               │
│  ▣ Public tenders (DNCP)                      │
│  ▣ Adjudications (DNCP)                       │
│  ▣ Active maquila factories (MIC)             │
│  ▣ Tax-registered businesses (SET/RUC)        │
│  ▣ IPS-affiliated employers (formal jobs)     │
│  ▣ Banks + ATMs + cooperatives (BCP)          │
│  ▣ Industry census density (MIC)              │
│  ▣ Crop area + yield (INBIO)                  │
└──────────────────────────────────────────────┘
```

**Why this matters**: a buyer looking at a $200K property near Caaguazú wants to know:
- Is there a school within 3 km? (INE locales educación)
- Is there a paved road? (MOPC + OSM)
- Is there a public hospital nearby? (INE locales salud)
- Are there formal employers within 30 km? (IPS)
- Is the area getting new public investment? (DNCP adjudicaciones)
- Are there active buyers competing for similar properties? (DNCP calls for similar zones)
- Is the area agriculturally productive? (INBIO)

This is **commercial intelligence**, not just real-estate listings.

## Implementation priority

| Layer | Phase | Source | Reason |
|---|---|---|---|
| DNCP calls + awards | 1 | DNCP API | Foundation for "what's being built" |
| Industry census | 1.5 | MIC | Per-district employment density |
| Maquila registry | 2 | MIC | Export sector overlay |
| Banking density | 1.5 | BCP | Financial inclusion overlay |
| Crop area + yield | 2 | INBIO | Agricultural productivity |
| RUC validation | 2 | SET | Listing quality control |
| IPS employers | 2.5 | IPS | Formal employment density |

## See also

- `docs/operations/properties-pipeline.md` — listings scraping
- `docs/operations/price-model.md` — price surface
- `docs/sources/agriculture.md` — INBIO deep-dive
- `docs/sources/infrastructure.md` — ANDE, ESSAP, MOPC