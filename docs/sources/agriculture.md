# Agriculture — Data Sources

## 1. INBIO — Instituto de Biotecnología Agrícola

| Field | Value |
|---|---|
| URL | https://inbio.org.py/ |
| Auth | None |
| License | Public info (with attribution) |
| Format | PDF reports + satellite-derived GeoTIFF |

**What we extract**:
- **Crop area** per departamento per zafra (Sep-Jun growing season)
- **Yield per hectare** by crop type (soja, maíz, trigo, girasol, sésamo, arroz, canola, ka'a he'ê)
- **Planting dates** (early/normal/late) — climate risk indicator
- **Cultivar distribution** by district

**Crops tracked**:
| Crop | Cadence | Notes |
|---|---|---|
| Soja | Per zafra | Largest export, ~9.3M ton zafra 2024-2025 |
| Maíz | Per zafra | 2nd-largest cereal |
| Trigo | Per zafra | Winter crop (zafriña) |
| Girasol | Per zafra | Oilseed |
| Sésamo | Per zafra | Specialty export |
| Arroz | Per zafra | Rice |
| Canola | Per zafra | Oilseed rotation |
| Ka'a he'ê (stevia) | Per year | Specialty crop |

**Map overlay design**:
- Per-departamento crop area (choropleth)
- Per-departamento yield (choropleth with 2-3 year trend)
- Per-district crop type diversity (heatmap)

## 2. INFONA — Instituto Forestal Nacional

| Field | Value |
|---|---|
| URL | https://www.infona.gov.py/ |
| Auth | None for public registry |
| Format | Shapefile + PDF |

**What we extract**:
- **Forest plantation registry** — Pino, Eucalyptus, other species
- **Harvest permits** — annual cut volumes per district
- **Native forest cover polygons**
- **Land-use change approvals**

**Use**:
- Agro-forestry intensity overlay
- Compliance vs deforestation overlay (cross-ref with Hansen + MapBiomas)
- Carbon stock rough estimate

## 3. SENAVE — Servicio Nacional de Calidad y Sanidad Vegetal y de Semillas

| Field | Value |
|---|---|
| URL | https://www.senave.gov.py/ |
| Auth | None for public catalog |
| Format | CSV / shapefile |

**What we extract**:
- **Phytosanitary status** by district (current pest/disease alerts)
- **Agrochemical registration** (where legal products are available)
- **Seed certification** registry (cultivar zone mapping)

**Use**: agricultural risk overlay by district (yellow = active phytosanitary alert).

## 4. MAG — Ministerio de Agricultura y Ganadería

| Field | Value |
|---|---|
| URL | https://www.mag.gov.py/ |
| Auth | Variable |
| License | Public info |

**What we extract**:
- **Agricultural extension offices** (extensionistas) — locations of MAG offices
- **Rural development programs** — per-district project tracking
- **Farming household survey** (Encuesta de Hogares Agropecuarios)

## 5. SENACSA — Servicio Nacional de Calidad y Salud Animal

| Field | Value |
|---|---|
| URL | https://www.senacsa.gov.py/ |
| Auth | Variable |
| License | Public info |

**What we extract**:
- **Cattle inventory** per distrito (heads of cattle)
- **Animal health status** (current outbreak alerts — aftosa, brucelosis)
- **Abattoir registry**

**Use**: livestock density overlay (Chaco vs Oriental).

## 6. Guyra Paraguay — Conservation NGO

| Field | Value |
|---|---|
| URL | https://www.guyra.org.py/ |
| Auth | Variable |
| License | Public info (NGO publications) |

**What we extract**:
- **IBA (Important Bird Areas)** polygons
- **Private protected areas** (complementing MADES public system)
- **Deforestation alerts** (real-time, validated by human review)

**Use**: conservation + biodiversity overlay; complements GBIF data.

## 7. SoilGrids 2.0 — ISRIC (international, PY-covered)

| Field | Value |
|---|---|
| URL | https://rest.isric.org/soilgrids/v2.0/ |
| Auth | None |
| License | CC BY 4.0 |
| Resolution | 250 m |
| Depth | 6 standard layers (0-5, 5-15, 15-30, 30-60, 60-100, 100-200 cm) |
| Properties | pH, SOC, clay, sand, silt, bulk density, CEC, nitrogen |

**Pitfall** (per `paraguay-open-data-fetch`): "Multi-property multi-depth queries return 500 or empty body. Issue ONE HTTP request per (property, depth) tuple. Per-call backoff 2s, 4s, 6s on failure."

**Use**: per-point soil composition lookup + raster visualization per property.

## 8. NASA Harvest / USDA FAS — Satellite-based agriculture monitoring

| Field | Value |
|---|---|
| URL | https://nasaharvest.org/ |
| Auth | None |
| License | Public info |

**What we extract**:
- **Crop calendars** for PY (planting/harvest dates by region)
- **Agricultural risk** (drought, flood, pest)

## Map overlay design

```
┌──────────────────────────────────────────────┐
│ AGRICULTURAL LAYERS (toggleable)              │
│                                               │
│  ▣ Crop area by type (INBIO)                  │
│  ▣ Yield per ha (INBIO)                       │
│  ▣ Crop diversity (Shannon index per dept)    │
│  ▣ Forest plantation area (INFONA)            │
│  ▣ Native forest cover (INFONA + Hansen)     │
│  ▣ Phytosanitary alerts (SENAVE)              │
│  ▣ Cattle density (SENACSA)                   │
│  ▣ Protected areas (Guyra + MADES)            │
│  ▣ Soil composition (SoilGrids)               │
│  ▣ Drought/flood risk (NASA Harvest)          │
└──────────────────────────────────────────────┘
```

## Why this matters for real-estate

A buyer evaluating a $300K property in San Pedro wants to know:
- What's the agricultural productivity of the soil? (INBIO + SoilGrids)
- Are there protected areas nearby that restrict land use? (Guyra + MADES)
- Is the district under a phytosanitary alert? (SENAVE)
- How intense is cattle farming? (SENACSA)
- Is the area forested or cultivated? (INFONA + Hansen)
- What's the climate risk? (NASA Harvest + CHIRPS)

## Implementation priority

| Layer | Phase | Source | Reason |
|---|---|---|---|
| Crop area (soja) | 1 | INBIO | Largest export, easy data |
| Forest plantation | 2 | INFONA | Forestry overlay |
| Cattle density | 2 | SENACSA | Chaco economics |
| SoilGrids lookup | 1 | ISRIC | Per-point depth (Phase 1 endpoint) |
| Protected areas | 1.5 | Guyra + MADES | Land-use restrictions |
| Phytosanitary alerts | 2.5 | SENAVE | Crop risk |
| Crop diversity | 3 | INBIO | Macro indicator |

## See also

- `docs/sources/businesses.md` — INBIO context
- `docs/sources/satellite.md` — Hansen, MapBiomas
- `docs/operations/properties-pipeline.md` — land-use + property context