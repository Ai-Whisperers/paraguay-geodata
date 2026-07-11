# Environment & Climate Risk — Data Sources

The map should overlay environmental risk — flooding, fire, air quality, drought, deforestation — because these directly affect property value and habitability.

## 1. MADES — Ministerio del Ambiente y Desarrollo Sostenible

| Field | Value |
|---|---|
| URL | https://www.mades.gov.py/ |
| Auth | Variable (heavy Cloudflare) |
| License | Public info |

### What we extract

| Layer | Type | Use |
|---|---|---|
| **Calidad del aire** | Point + time-series | Air quality stations (PM2.5, PM10, NO₂, O₃) |
| **Estaciones meteorológicas** | Point | DINAC cross-ref |
| **Cuerpos de agua** | Polygon | Rivers, lakes, wetlands (often higher accuracy than OSM) |
| **Áreas protegidas (SNP)** | Polygon | National Protected Areas System |
| **EIA filings** | Polygon | Industrial sites with environmental licenses |
| **Pasivos ambientales** | Point/Polygon | Mining + industrial contamination |

**Pitfall**: MADES portal uses Cloudflare protection + Nuxt.js SPA. Headless Chrome required per `paraguay-research-toolkit` skill.

## 2. DINAC — Dirección Nacional de Meteorología

| Field | Value |
|---|---|
| URL | https://www.dinac.gov.py/ |
| Auth | None for most public data |
| Format | CSV per station |

### What we extract

| Layer | Type | Use |
|---|---|---|
| **Estaciones meteorológicas** | Point | Weather station locations |
| **Datos horarios** | Time-series | Temp, humidity, pressure, wind |
| **Lluvia diaria** | Time-series | Daily rainfall per station |
| **Alertas meteorológicas** | Time-series | Severe weather warnings |
| **Radar meteorológico** | Image (MeteoStar) | Doppler radar images (not raster extractable) |

**Implementation**: `tools/fetch_dinac_weather.py` — daily cron, fetches the latest 7 days per station.

## 3. FIRMS — NASA Fire Information for Resource Management System

| Field | Value |
|---|---|
| URL | https://firms.modaps.eosdis.nasa.gov/api/country/csv/<API_KEY>/VIIRS_SNPP_NRT/PRY/24h |
| Auth | FIRMS MAP_KEY (free, NASA Earthdata account) |
| License | Public domain |
| Resolution | 375 m (VIIRS) + 1 km (MODIS) |
| Refresh | Daily |

**What we extract**:
- **Active fire hotspots** (last 7 days per tile)
- **Fire risk** (last 30 days per district)

**Use**:
- Real-time wildfire overlay (Chaco burn season: Jul-Oct)
- Property insurance overlay (within 5 km of fire hotspot = higher risk)
- Agricultural fire detection (cane + forest)

## 4. CHIRPS — Climate Hazards Group InfraRed Precipitation with Station data

| Field | Value |
|---|---|
| URL | https://www.chc.ucsb.edu/data/chirps |
| Auth | None |
| Format | GeoTIFF |
| Resolution | 5 km daily, 0.05° monthly |
| Years | 1981-present |

**What we extract**:
- **Monthly rainfall** per tile (per-dept aggregate)
- **Drought periods** (SPI — Standardized Precipitation Index)
- **Flood periods** (extreme rainfall events)
- **Long-term normals** (1991-2020 baseline)

**Use**:
- Drought risk overlay
- Flood risk overlay
- Agricultural productivity signal (correlation with INBIO yield)

## 5. ERA5 / ERA5-Land — ECMWF Reanalysis

| Field | Value |
|---|---|
| URL | https://cds.climate.copernicus.eu/ |
| Auth | CDS account (free) |
| Format | GRIB / NetCDF |
| Resolution | 0.25° (ERA5), 0.1° (ERA5-Land) |
| Years | 1940-present (ERA5), 1950-present (ERA5-Land) |

**What we extract**:
- **Soil moisture** (volumetric m³/m³) — agricultural drought indicator
- **Evapotranspiration** — water budget
- **Air temperature** (2 m above ground) — heat island analysis
- **Wind speed + direction** — wind energy + pesticide drift

## 6. Hansen GFC + MapBiomas — Deforestation + land cover

Already covered in `satellite.md` and `agriculture.md`. Cross-references here:

| Use | Sources |
|---|---|
| Deforestation alerts | Hansen loss year + FIRMS fire proximity |
| Native forest cover | MapBiomas class 3 (forest formation) + Hansen |
| Chaco burn risk | FIRMS VIIRS + Hansen loss year + dry-season rainfall |
| Atlantic Forest recovery | MapBiomas regrowth class + Guyra data |

## 7. JRC Global Surface Water — Flooding

| Field | Value |
|---|---|
| URL | https://global-surface-water.appspot.com/download |
| Resolution | 30 m |
| Years | 1984-2021 |

**What we extract**:
- **Water occurrence** (frequency of water presence)
- **Water seasonality** (months per year with water)
- **Water recurrence** (transient vs permanent)
- **Maximum water extent** (extreme flood footprint)

**Use**:
- **Flood risk overlay** — properties near seasonal water extent
- **Wetland identification** — distinct from rivers
- **Drought year detection** — water shrinkage 2020-2021 Chaco

## 8. NASA POWER — Solar + Climate for any point

| Field | Value |
|---|---|
| URL | https://power.larc.nasa.gov/ |
| Auth | None |
| Format | CSV / JSON |
| Variables | Solar irradiance, temperature, wind, humidity |

**What we extract**:
- **Annual solar irradiance** per (lat, lon) → solar PV potential
- **Monthly temperature** extremes (urban heat + climate risk)

## 9. Climate change projections (CMIP6 downscaled)

| Field | Value |
|---|---|
| URL | Various (CMIP6 data portals) |
| Auth | Variable (most free) |

**Use**: per-dept projected change in rainfall + temperature for 2050 + 2100 (paraguay-specific downscaling via Climate-PRO or similar). Phase 3 deliverable.

## 10. AON / Mapfre / Sancor — Insurance risk

| Field | Value |
|---|---|
| URL | https://www.aon.com/ (regional Paraguay office +595 21 417 9000) |
| Auth | Commercial |

**Use**: per-district catastrophic risk model (flood, hail, drought, fire). **Not free**, but extremely valuable for insurance overlay.

## Map overlay design

```
┌──────────────────────────────────────────────┐
│ ENVIRONMENTAL LAYERS (toggleable)            │
│                                               │
│  ▣ Air quality stations (MADES)               │
│  ▣ Active fires (FIRMS)                       │
│  ▣ Monthly rainfall (CHIRPS)                  │
│  ▣ Soil moisture (ERA5)                       │
│  ▣ Flood risk (JRC extent + rainfall)         │
│  ▣ Deforestation year (Hansen)                │
│  ▣ Water occurrence (JRC)                     │
│  ▣ Protected areas (MADES + Guyra)            │
│  ▣ Solar irradiance (NASA POWER)              │
│  ▣ Climate projections 2050/2100 (CMIP6)      │
└──────────────────────────────────────────────┘
```

## Why this matters for real-estate

| Question | Source |
|---|---|
| Is this property in a flood zone? | JRC + DINAC |
| How often does it burn nearby? | FIRMS 7d + Hansen 5y |
| What's the air quality? | MADES air stations |
| Is the soil drought-prone? | ERA5 soil moisture + CHIRPS SPI |
| Is the area protected? | MADES + Guyra |
| What's the solar potential? | NASA POWER |
| What's the climate projection? | CMIP6 downscaled |

## Implementation priority

| Layer | Phase | Source | Reason |
|---|---|---|---|
| FIRMS fire hotspots | 1 | NASA | Easy, daily, high-value |
| Hansen loss/gain | 1 | Hansen | Already in tile fabric |
| JRC waterbodies | 1 | JRC | Already in tile fabric |
| Air quality stations | 1.5 | MADES | Urban only |
| Monthly rainfall | 2 | CHIRPS | Time-series overlay |
| Soil moisture | 2.5 | ERA5-Land | Agricultural overlay |
| Climate projections | 3 | CMIP6 | Long-term risk |
| Insurance risk | 3 | AON/Mapfre | Phase 3 paid API |

## See also

- `docs/sources/satellite.md` — base raster sources
- `docs/sources/agriculture.md` — agricultural risk
- `docs/sources/businesses.md` — DNCP for active construction