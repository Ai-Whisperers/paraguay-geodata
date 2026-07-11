# Socioeconomic — Data Sources

The map should overlay demographic + economic + service-coverage data because property values are 50% driven by these.

## 1. INE — Instituto Nacional de Estadística

### EPH (Encuesta Permanente de Hogares)

| Field | Value |
|---|---|
| URL | https://www.ine.gov.py/microdatos/ |
| Period | 2017-2026 quarterly + annual |
| Format | CSV / SAV / SPSS |
| License | Public info (with attribution) |
| Sample | ~5,000-8,000 households per quarter |

**What we extract**:
- **Ingreso familiar** (household income)
- **Empleo formal/informal** (employment status)
- **Pobreza + indigencia** (poverty + indigence rates)
- **Educación** (years of schooling)
- **Salud** (insurance coverage, access to services)
- **Vivienda** (housing tenure, quality)

**Per-department aggregation**: 17 departamentos + Asunción.

### IPM (Índice de Pobreza Multidimensional)

| Field | Value |
|---|---|
| URL | https://www.ine.gov.py/microdatos/ |
| Period | 2016-2024 annual |
| Format | CSV / DTA / SAV |

**What we extract**:
- 4 dimensions (trabajo+seguridad social, vivienda+servicios, salud+ambiente, educación)
- Per-department IPM rate + intensity

**Map overlay design**:
- Choropleth IPM rate per departamento
- 4 sub-layers toggleable (each dimension)
- Per-district granularity where data permits

### CNPV — Censo Nacional de Población y Viviendas

| Field | Value |
|---|---|
| URL | https://www.ine.gov.py/microdatos/ |
| Year | 2022 (latest) |
| Format | CSV |

**What we extract**:
- Population by age + gender per district
- Housing quality (material, tenure, occupancy)
- Utilities (water, sewer, electricity)
- Education attainment
- Migration patterns

### Proyecciones de Población

| Field | Value |
|---|---|
| URL | https://www.ine.gov.py/microdatos/ |
| Format | XLSX |

**What we extract**:
- Population projections by departamento (forward 25 years)
- Growth rate overlay

## 2. DGEEC — Migrated to INE (2024)

No separate data sources.

## 3. ENDE (Encuesta Nacional de Desarrollo) — historic

Older survey; superseded by EPH. Skip.

## 4. ENSIMUP 2021 — Women's situation survey

| Field | Value |
|---|---|
| URL | https://www.ine.gov.py/microdatos/ |
| Year | 2021 (one-shot) |
| Format | CSV / SPSS |

**What we extract**: women's economic participation + domestic violence indicators (per district).

## 5. MSPBS — Ministerio de Salud Pública y Bienestar Social

| Field | Value |
|---|---|
| URL | https://www.mspbs.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

- **Hospital network** (public + private) — locations, capacity
- **Health centers** — primary care locations
- **Disease surveillance** (weekly bulletins — dengue, COVID, etc.)
- **Vaccination coverage** per district

**Use**: health service overlay + outbreak alerts.

## 6. MEC — Ministerio de Educación y Ciencias

| Field | Value |
|---|---|
| URL | https://www.mec.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

- **School locations** (already in INE locales educación)
- **School performance** (Pruebas Aprender — standardized test results)
- **Education programs** (per district)
- **Literacy rates** per district

## 7. SNNA — Secretaría Nacional de la Niñez y Adolescencia

| Field | Value |
|---|---|
| URL | https://www.snna.gov.py/ |
| Auth | Variable |
| License | Public info |

**What we extract**: child labor + child poverty indicators per district.

## 8. SEN — Secretaría de Emergencia Nacional

| Field | Value |
|---|---|
| URL | https://www.sen.gov.py/ |
| Auth | Variable |
| License | Public info |

**What we extract**:
- **Emergency declarations** per district
- **Disaster response** (flooding, fire, severe weather)

## 9. BCP — Banco Central del Paraguay

| Field | Value |
|---|---|
| URL | https://www.bcp.gov.py/ |
| Format | XLSX |

### What we extract

| Indicator | Period | Use |
|---|---|---|
| **IPC** (consumer price index) | Monthly | Inflation per region |
| **Tipo de cambio** PYG/USD | Daily | FX for price conversion |
| **PIB per cápita** | Per quarter | Per-dept economic output |
| **Depósitos bancarios** | Monthly | Banking depth per dept |
| **Préstamos al sector privado** | Monthly | Credit penetration |
| **Remesas familiares** | Monthly | Migration impact |

## 10. INAMU — Instituto Nacional de la Mujer

| Field | Value |
|---|---|
| URL | https://www.inamu.gov.py/ |
| License | Public info |

**What we extract**: women-specific socioeconomic indicators per department.

## 11. SENAD — Secretaría Nacional Antidrogas

| Field | Value |
|---|---|
| URL | https://www.senad.gov.py/ |
| License | Public info |

**What we extract**: per-district drug activity reports (insecurity proxy).

## 12. Policia Nacional — crime statistics

| Field | Value |
|---|---|
| URL | https://www.policianacional.gov.py/ |
| Auth | Variable |
| License | Public info |

**What we extract**: per-district crime statistics (annual reports).

**Use**: security overlay (often a property value driver).

## 13. Migraciones — Dirección General de Migraciones

| Field | Value |
|---|---|
| URL | https://www.migraciones.gov.py/ |
| Auth | Variable |
| License | Public info |

**What we extract**: immigration entry/exit data per border crossing (cross-ref with MOPC border posts).

## 14. AHK Paraguay — German chamber (foreign investment)

| Field | Value |
|---|---|
| URL | https://www.paraguay.ahk.de/ |
| Auth | None for member directory |
| License | Public info |

**What we extract**: member companies (German-PY businesses) — location-based.

**Use**: foreign investment activity overlay.

## 15. UIP — Unión Industrial Paraguaya

| Field | Value |
|---|---|
| URL | https://uip.org.py/ |
| Auth | None for member directory |
| License | Public info |

**What we extract**: UIP member companies (industrial sector).

**Use**: industrial sector employment overlay.

## Map overlay design

```
┌──────────────────────────────────────────────┐
│ SOCIOECONOMIC LAYERS (toggleable)            │
│                                               │
│  ▣ Population density (INE CNPV 2022)         │
│  ▣ Population projection 2050 (INE)           │
│  ▣ IPM poverty rate (INE 2024)                │
│  ▣ Per-capita income (EPH)                    │
│  ▣ Formal employment rate (EPH)               │
│  ▣ Banking density (BCP)                      │
│  ▣ School locations (INE locales educación)   │
│  ▣ Health facilities (INE locales salud)      │
│  ▣ Crime statistics (Policia Nacional)        │
│  ▣ Foreign-investment footprint (AHK, UIP)    │
└──────────────────────────────────────────────┘
```

## Why this matters for real-estate

| Question | Source |
|---|---|
| What's the demographic trend? | INE proyecciones |
| What's the poverty rate? | INE IPM |
| What's the income? | EPH |
| Is there school access? | INE locales educación |
| Is there hospital access? | INE locales salud |
| Is it safe? | Policia Nacional |
| What's the employment base? | EPH + IPS + DNCP |
| Are there foreign investors? | AHK + UIP |

## Implementation priority

| Layer | Phase | Source | Reason |
|---|---|---|---|
| Departamentos (boundary) | 1 | INE | Foundational admin |
| Distritos (boundary) | 1 | INE | Foundational admin |
| Locales educación/salud/policial | 1 | INE | Built infrastructure |
| Population density | 1 | INE CNPV 2022 | Per-dept choropleth |
| IPM poverty | 1.5 | INE IPM 2024 | Macro overlay |
| Banking density | 2 | BCP | Financial inclusion |
| Crime statistics | 2.5 | Policia Nacional | Security overlay |
| Per-capita income | 3 | EPH | Macro overlay |
| Foreign investment | 2.5 | AHK + UIP | Specialised overlay |

## See also

- `docs/sources/administrative.md` — INE administrative layers
- `docs/sources/businesses.md` — commercial activity
- `docs/sources/environment.md` — risk overlays