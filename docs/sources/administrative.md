# Administrative Boundaries — Data Sources

## 1. INE — Instituto Nacional de Estadística (the official census source)

| Field | Value |
|---|---|
| URL | https://www.ine.gov.py/microdatos/ |
| Auth | None |
| License | "Licencia de Uso de la Información Pública" (public info use license) |
| Format | Shapefile / KML / **GeoJSON** |
| Refresh | Per census (2012, 2022 revision) |

### Layer inventory

| Layer | Type | Available? | Use |
|---|---|---|---|
| **Departamentos (17)** | Polygon | ✅ GeoJSON | Tier-1 admin overlay |
| **Distritos (~262)** | Polygon | ✅ GeoJSON | Tier-2 admin overlay |
| **Barrios / Localidades** | Polygon | ✅ GeoJSON | Urban neighborhoods |
| **Manzanas** | Polygon | ✅ GeoJSON (urban only) | Census block + land use |
| **Ciudades** | Point | ✅ GeoJSON | Urban center points |
| **Vías principales** | LineString | ✅ GeoJSON | Road network backbone |
| **Hidrografía** | LineString | ✅ GeoJSON | Rivers, streams |
| **Comunidades indígenas** | Polygon | ✅ GeoJSON | Indigenous territories (legal weight) |
| **Locales de Salud** | Point | ✅ GeoJSON | Health facility locations |
| **Locales Policiales** | Point | ✅ GeoJSON | Police stations |
| **Locales de Educación** | Point | ✅ GeoJSON | Schools |

**Implementation plan** (Phase 1.5):
- Download per-departamento GeoJSON
- Convert to single national GeoJSON per layer (concatenate)
- Ship as base layers (always visible by default at appropriate zoom)
- Hierarchical styling: dept-level (10 km zoom), distrito (5 km), barrio (1 km), manzana (100 m)

### Census data

| Dataset | Period | Format | Use |
|---|---|---|---|
| **EPHC (Encuesta Permanente de Hogares Continua)** | 2017-2026 (quarterly + annual) | CSV / SAV / SPSS | Income, employment, demographics |
| **IPM (Índice de Pobreza Multidimensional)** | 2016-2024 (annual) | CSV / DTA / SAV | 4-dimension poverty index |
| **CNPV 2022** | one-shot 2022 | CSV | Census population, housing |
| **Proyecciones de Población** | forward | XLSX | Population projections by dept/district |
| **ENSIMUP 2021** | one-shot | CSV | Women's situation survey |

### Code reference

- **DPA (División Política Administrativa) codes** — codigos geográficos CNPV 2012
- District + barrio codes feed into the property schema (`attrs.district_code` field)

**Where it goes**: `tools/fetch_ine_admin.py` (Phase 1.5)

## 2. DGEEC — Dirección General de Estadística, Encuestas y Censos

| Field | Value |
|---|---|
| URL | https://www.ine.gov.py/ (now merged with INE since 2024) |
| Status | Migrated to INE |
| Cartography | All on INE |

We treat INE as the single source of administrative boundaries.

## 3. MADES — Ministerio del Ambiente y Desarrollo Sostenible

| Field | Value |
|---|---|
| URL | https://www.mades.gov.py/ |
| Auth | Variable — some portals require registration |
| License | Public info |

**Layers potentially available**:
- EIA (Estudio de Impacto Ambiental) filings → industrial sites
- Forest reserve boundaries
- Protected areas (SNP — Sistema Nacional de Áreas Protegidas)
- Water quality monitoring stations
- Air quality monitoring stations (see `environment.md`)

**Caveat**: MADES site has heavy Cloudflare protection — needs headless Chrome per `paraguay-research-toolkit` skill.

## 4. INFONA — Instituto Forestal Nacional

| Field | Value |
|---|---|
| URL | https://www.infona.gov.py/ |
| Auth | None for most public data |
| License | Public info |

**Layers**:
- Forest plantation registry (Pino, Eucalyptus, other)
- Forest harvesting permits (annual cuts)
- Native forest cover polygons

**Use**: forest industry activity overlay. Tracks industrial forestry vs subsistence.

## 5. SENAVE — Servicio Nacional de Calidad y Sanidad Vegetal y de Semillas

| Field | Value |
|---|---|
| URL | https://www.senave.gov.py/ |
| Auth | None for public catalog |
| License | Public info |

**Layers**:
- Phytosanitary status by district (current)
- Agrochemical registration
- Seed certification registry
- Cultivar zones

**Use**: agricultural risk by district + crop zoning.

## 6. SEAM (now MADES) — see above

## What we DO NOT integrate

- Voter registration data (TSE) — political sensitivity
- Per-individual health records (MSPBS) — PII
- Per-individual education records (MEC) — PII
- Per-household tax records (SET) — PII

## Implementation priority

| Layer | Phase | Source | Reason |
|---|---|---|---|
| Departamentos | 1 | INE | Tier-1 admin overlay, foundational |
| Distritos | 1 | INE | Tier-2 admin, needed for listings cross-ref |
| Barrios | 1 | INE | Urban granularity for properties |
| Manzanas | 1.5 | INE | Census block, land use, urban heat |
| Locales Salud/Policial/Educación | 1.5 | INE | Built infrastructure overlays |
| Comunidades indígenas | 2 | INE | Legal boundaries, agricultural restrictions |
| Forest plantations INFONA | 2 | INFONA | Agro-forestry overlay |
| IPM poverty index | 1.5 | INE | Property valuation heat overlay |

## See also

- `docs/sources/socioeconomic.md` — IPM, EPH
- `docs/sources/environment.md` — MADES
- `docs/sources/agriculture.md` — SENAVE, INFONA
- `tools/fetch_ine_admin.py` — implementation stub (Phase 1)