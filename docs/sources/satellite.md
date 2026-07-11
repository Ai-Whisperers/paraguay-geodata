# Satellite + Remote Sensing — Data Sources

## Confirmed-live (Phase 1 priority)

### DEM — Copernicus GLO-30 + NASADEM

| Field | Value |
|---|---|
| Source | Microsoft Planetary Computer |
| Auth | Signed URL (free) |
| Resolution | 30 m |
| Coverage | Global, all of Paraguay |
| Format | COG (Cloud Optimized GeoTIFF) |
| License | Free + open |

**URLs**:
- `https://planetarycomputer.microsoft.com/dataset/cop-30`
- `https://planetarycomputer.microsoft.com/dataset/nasadem` (backup, same 30m)

**Use**: tile DEM, derive streams/cerros/contours/slope/aspect/hillshade via `tools/build_*` family. Already in tile-index.

### Esri World Imagery

| Field | Value |
|---|---|
| Source | ArcGIS REST Services |
| Auth | None (free for tiles ≤ z=19) |
| Resolution | z=17 = 1 m/px, z=18 = 0.5 m/px, z=19+ empty tiles in rural PY |
| Coverage | Global |
| Format | PNG tile pyramid |

**URL pattern**: `https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`

**Use**: visual basemap + LOD2 (z=17) for urban, LOD3 (z=18) for parcel-detail.

### Sentinel-2 L2A

| Field | Value |
|---|---|
| Source | ESA Copernicus via Element84 STAC + Microsoft Planetary Computer |
| Auth | Signed URL (free) |
| Resolution | 10 m (RGB+NIR), 20 m (red-edge), 60 m (cirrus/aerosol) |
| Coverage | Global, revisit ~5 days |
| Format | COG-JP2 |

**STAC search**: `pystac_client.Client.open('https://planetarycomputer.microsoft.com/stac/v1')`

**Filter**: PY UTM 21J = MGRS tile code `_T21J*` (per the `satellite-to-blender-pipeline` skill pitfall: STAC's `sentinel:utm_zone` field is NOT queryable — filter post-search by item id).

**Use**: NDVI canopy, RGB composites, cloud mask via SCL band.

### OSM (OpenStreetMap)

| Field | Value |
|---|---|
| Source | OpenStreetMap contributors |
| Auth | None (Overpass public API) |
| Coverage | Variable — dense in urban, sparse in Chaco |
| Format | GeoJSON via Overpass |

**URL**: `https://overpass-api.de/api/interpreter` (POST with x-www-form-urlencoded, NOT GET — per `paraguay-open-data-fetch` pitfall).

**Use**: roads, buildings, water, waterways, places, POIs, trees, landuse.

### MapBiomas Paraguay

| Field | Value |
|---|---|
| URL | https://plataforma.mapbiomas.org/ |
| Auth | None |
| License | CC BY 4.0 |
| Resolution | 30 m, annual classification |
| Years | 1985-2023 (Chaco from 2000) |
| Format | GeoTIFF download per year + per biome |

**Use**: land cover classification. Toggle in viewer (selectable year).

### Hansen GFC

| Field | Value |
|---|---|
| URL | https://storage.googleapis.com/umd_hansen_dl4/ |
| Auth | None (GCS public bucket) |
| License | CC BY 4.0 |
| Resolution | 30 m |
| Format | GeoTIFF |

**Layers**: `treecover2010`, `loss`, `gain`, `datamask`

**Use**: canopy 2010 baseline + loss/gain year-by-year.

### JRC Global Surface Water

| Field | Value |
|---|---|
| URL | https://global-surface-water.appspot.com/download |
| Auth | None |
| License | Free + open |
| Resolution | 30 m |
| Years | 1984-2021 |
| Format | GeoTIFF tiles |

**Use**: waterbodies polygons + surface water change.

### HydroSHEDS

| Field | Value |
|---|---|
| URL | https://www.hydrosheds.org/products/hydrosheds-global |
| Auth | None (CC BY 4.0) |
| Resolution | 15" (~500 m) for global, 3" (~90 m) for select regions |
| Format | GeoTIFF + shapefile |

**Use**: flow direction, accumulation → quebradas + catchments.

### NASA FIRMS

| Field | Value |
|---|---|
| URL | https://firms.modaps.eosdis.nasa.gov/api/country/csv/<API_KEY>/VIIRS_SNPP_NRT/PRY/24h |
| Auth | FIRMS MAP_KEY (free, NASA Earthdata account) |
| License | Public domain |
| Resolution | 375 m (VIIRS) + 1 km (MODIS) |
| Refresh | Daily CSV per country |

**Use**: fire hotspots, last 7 days per tile.

### GBIF

| Field | Value |
|---|---|
| URL | https://api.gbif.org/v1/occurrence/search?country=PY |
| Auth | None |
| License | Varies per record (CC0 / CC BY / CC BY-NC) |
| Refresh | Real-time |

**Use**: species observations within each tile bbox.

## Confirmed-available (Phase 1/2)

### MODIS / MOD11 / MOD16 — Temperature + ET

| Field | Value |
|---|---|
| URL | https://modis.gsfc.nasa.gov/ |
| Auth | None |
| Format | HDF4 / GeoTIFF |
| Resolution | 1 km (MOD11 LST), 500 m (MOD16 ET) |

**Use**: land surface temperature, evapotranspiration → agricultural productivity, urban heat.

### CHIRPS — Rainfall

| Field | Value |
|---|---|
| URL | https://www.chc.ucsb.edu/data/chirps |
| Auth | None |
| Resolution | 5 km daily, 0.05° monthly |
| Years | 1981-present |

**Use**: rainfall raster per month / per year → agricultural risk, drought overlay.

### NASA POWER — Solar + Climate

| Field | Value |
|---|---|
| URL | https://power.larc.nasa.gov/ |
| Auth | None |
| Format | CSV / JSON per point |
| Variables | Solar radiation, temperature, wind, humidity |

**Use**: solar PV potential (per-tile centroid), agronomic risk.

### SRTM

| Field | Value |
|---|---|
| URL | https://earthexplorer.usgs.gov/ |
| Auth | None |
| Resolution | 30 m (SRTM 1") + 90 m (SRTM 3") |
| Format | GeoTIFF |
| Coverage | Lat -60 to +60 |

**Use**: backup DEM (SRTM 1" → derived contours, lower quality than GLO-30 but available offline).

### GEDI — Canopy heights

| Field | Value |
|---|---|
| URL | https://gedi.umd.edu/ |
| Auth | NASA Earthdata (free) |
| Format | HDF5 |
| Resolution | ~25 m footprint, transects |

**Use**: forest height in select regions (not continuous coverage).

### CHELSA — Climate

| Field | Value |
|---|---|
| URL | https://chelsa-climate.org/ |
| Auth | None |
| Format | GeoTIFF |
| Resolution | 30" (~1 km) |
| Years | 1979-2019 |

**Use**: long-term climate normals (temperature, precipitation).

### ERA5 / ERA5-Land

| Field | Value |
|---|---|
| URL | https://cds.climate.copernicus.eu/ |
| Auth | CDS account (free) |
| Format | GRIB / NetCDF |
| Resolution | 0.25° (ERA5), 0.1° (ERA5-Land) |
| Years | 1940-present (ERA5), 1950-present (ERA5-Land) |

**Use**: high-res climate variables (soil moisture, ET).

## Research-needed (Phase 1.5+)

- Paraguay-specific deforestation alerts (Guyra Paraguay + INFONA)
- SoilGrids 2.0 (already cited) — soil composition for agriculture
- Paraguay-specific birding data (Guyra Paraguay BirdLife Intl partner)
- Climate-PRO — Paraguay-specific downscaled projections

## Already in LQV pipeline (proven)

The LQV repo already proved these sources work at 10×10 km:
- Copernicus GLO-30 → DEM
- Esri HD → visual basemap
- Sentinel-2 → NDVI, RGB
- OSM → roads, buildings, water
- MapBiomas → land cover
- Hansen GFC → canopy + loss/gain
- JRC → waterbodies
- GBIF → species
- NASA FIRMS → fire
- SoilGrids → soil composition

## See also

- `~/la-quebrada-viva/docs/site_data/` — LQV data lake (per-source folder layout)
- `~/la-quebrada-viva/docs/site_data_*/` — LQV per-source snapshots
- `~/.hermes/skills/devops/satellite-to-blender-pipeline/SKILL.md` — technique owner
- `~/.hermes/skills/paraguay-open-data-fetch/SKILL.md` — source catalogue skill