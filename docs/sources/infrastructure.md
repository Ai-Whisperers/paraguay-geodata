# Infrastructure — Data Sources

The map should overlay built infrastructure — utilities, roads, transport — because property value is shaped 70% by what's nearby, not just the parcel itself.

## 1. MOPC — Ministerio de Obras Públicas y Comunicaciones

| Field | Value |
|---|---|
| URL | https://www.mopc.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

| Layer | Type | Use |
|---|---|---|
| **Rutas nacionales** | LineString | Highway network (Ruta 1, 2, 3, ... 9 + Transchaco) |
| **Rutas departamentales** | LineString | Secondary paved + ripio roads |
| **Caminos vecinales** | LineString | Tertiary roads (variable quality) |
| **Puentes** | Point | Bridge inventory |
| **Aeropuertos** | Point | Silvio Pettirossi + regional |
| **Obras en ejecución** | Polygon/LineString | Active construction (cross-ref DNCP) |

**Pitfall**: MOPC site is heavy Cloudflare + Nuxt.js SPA — needs headless Chrome per `paraguay-research-toolkit` skill.

### Implementation plan

- Static OSM roads data (already in tile fabric via Overpass)
- Cross-reference MOPC official road class with OSM highway tag
- MOPC roads → `data/mopc/roads_<date>.geojson` (higher accuracy than OSM in rural areas)

## 2. ANDE — Administración Nacional de Electricidad

| Field | Value |
|---|---|
| URL | https://www.ande.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

| Layer | Type | Use |
|---|---|---|
| **Red de alta tensión** (220 kV, 66 kV) | LineString | Power transmission backbone |
| **Red de media tensión** (23 kV, 13.2 kV) | LineString | Distribution feeders |
| **Subestaciones** | Point | Substations |
| **Cobertura por distrito** | Polygon | % electrified |
| **Tarifas** | Per region | Electricity cost overlay |

**Use**:
- "Is this property within 1 km of medium-voltage power?" (buildability + value)
- "What's the electrical reliability in this district?" (cross-ref with outages — Phase 2.5)
- "What capacity is available?" (industrial property assessment)

### Implementation plan

- `tools/fetch_ande_network.py` — shapefile download → GeoJSON
- `tools/fetch_ande_coverage.py` — per-distrito electrification %
- `tools/build_power_distance.py` — distance-to-power raster per tile

## 3. ESSAP — Empresa de Servicios Sanitarios del Paraguay

| Field | Value |
|---|---|
| URL | https://www.essap.com.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

| Layer | Type | Use |
|---|---|---|
| **Red de agua potable** | LineString | Urban water network |
| **Cobertura por distrito** | Polygon | % with potable water |
| **Plantas de tratamiento** | Point | Treatment facilities |

**Use**: per-district water access overlay + industrial property check (capacity).

## 4. COPACO — Compañía Paraguaya de Comunicaciones

| Field | Value |
|---|---|
| URL | https://www.copaco.com.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

- **Fiber optic backbone** (mostly along Ruta 2)
- **ADSL coverage** by district
- **Mobile coverage** (cross-ref with Tigo/Personal/Claro)

**Use**: connectivity overlay (important for rural land).

## 5. Tigo / Personal / Claro — Mobile operators

| Field | Value |
|---|---|
| Tigo | https://www.tigo.com.py/ |
| Personal | https://www.personal.com.py/ |
| Claro | https://www.claro.com.py/ |

### What we extract

- **4G/5G coverage** by district (typically published as press release maps)
- **Tower locations** (sometimes published as "we built N towers here")

**Use**: mobile connectivity overlay. OpenSignal + Sensorly community data may be a better source.

## 6. DINAC — Dirección Nacional de Aeronáutica Civil

| Field | Value |
|---|---|
| URL | https://www.dinac.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

- **Aeropuerto locations** (already partially in MOPC)
- **Air traffic** per airport
- **Flight routes** (may require commercial flight data — paywall)

## 7. Petropar — Petróleos Paraguayos

| Field | Value |
|---|---|
| URL | https://www.petropar.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

- **Fuel station locations**
- **Fuel prices** (weekly, by station)
- **Pipeline network** (couldn't confirm publicly available)

**Use**: fuel access + cost overlay.

## 8. Public transport — SETAMA / Viceministerio de Transporte

| Field | Value |
|---|---|
| URL | http://www.vmt.gov.py/ |
| Auth | Variable |
| License | Public info |

### What we extract

- **Bus route data** (varies by city)
- **Asunción metropolitan bus** (informal — hard to source reliably)

## Map overlay design

```
┌──────────────────────────────────────────────┐
│ INFRASTRUCTURE LAYERS (toggleable)           │
│                                               │
│  ▣ Power grid (ANDE) — by voltage             │
│  ▣ Water network (ESSAP) — urban only         │
│  ▣ Roads (MOPC + OSM) — by class              │
│  ▣ Bridges + culverts (MOPC)                  │
│  ▣ Mobile coverage (Tigo/Personal/Claro)      │
│  ▣ Fiber backbone (COPACO)                    │
│  ▣ Fuel stations (Petropar)                   │
│  ▣ Airports (DINAC + MOPC)                    │
│  ▣ Distance-to-power raster (derived)         │
└──────────────────────────────────────────────┘
```

## Why this matters for real-estate

| Question | Source |
|---|---|
| Is there paved road access? | MOPC + OSM |
| How far to electrical connection? | ANDE + derived distance |
| Is there municipal water? | ESSAP + INE |
| Mobile signal strength? | Tigo/Personal/Claro coverage maps |
| Distance to nearest hospital? | INE locales salud + routing |
| Distance to nearest school? | INE locales educación + routing |
| Industrial capacity nearby? | ANDE transformer + ESSAP water main |

## Implementation priority

| Layer | Phase | Source | Reason |
|---|---|---|---|
| OSM roads | 1 | Overpass | Already in tile fabric |
| Distance-to-power | 1 | derived from OSM power lines | Foundation overlay |
| Distance-to-water | 1 | derived from OSM water lines | Foundation overlay |
| ANDE grid shapefile | 2 | ANDE | Higher accuracy than OSM |
| Locales Salud/Educación/Policial | 1 | INE | Built infrastructure |
| Fuel stations | 1.5 | Petropar + OSM | Convenience |
| ESSAP coverage | 2 | ESSAP | Urban only |
| Fiber backbone | 2.5 | COPACO | Telecoms |

## See also

- `docs/sources/businesses.md` — DNCP active construction
- `docs/sources/satellite.md` — base layers
- `docs/sources/environment.md` — environmental risk