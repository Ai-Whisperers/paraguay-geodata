# Paraguay Geodata — LQV Data Migration Plan

**Live:** https://geodata.paragu-ai.com/ · **Source:** https://lqv-walkthrough.pages.dev/

This document catalogs every data product in the **La Quebrada Viva** repo (Paraguarí, 62 ha parcel) that we can scale to national Paraguay, plus new regulatory/ordinance data Lucía needs for construction feasibility.

## Source analysis: hillshade_parcel.jpg

Located at `/root/repos/la-quebrada-viva/splats/exports/web/data/hillshade_parcel.jpg`:

- **Format:** JPEG, 706×706 px, 76 KB, 8-bit grayscale
- **Source:** Copernicus GLO-30 DEM at 5m resolution (fused from raw 30m tiles)
- **Bounds:** -57.038 to -57.024 lon, -25.617 to -25.602 lat (62 ha LQV parcel + 100m buffer)
- **How it's rendered:** `L.imageOverlay` with `opacity: 0.65`, z-index managed via `bringToBack()`
- **Loader:** `build_topology_hillshade.py` fetches DEM tiles from Planetary Computer, computes Horn's method hillshade, saves JPEG + bounds JSON
- **Coverage:** Only 1.6 km × 1.6 km — useful for one property, useless for the country

## Why scale to Paraguay

Three reasons:

1. **Topographic context**: buyers/developers need to see slope, drainage, viewsheds at any property — not just LQV
2. **Construction feasibility (Lucía's feedback)**: "si quieren construir deben conocer la ordenanza de construccion de la zona" — without terrain, zoning, soil, climate data, you can't answer "what can I build here"
3. **Defensible pricing**: $/ha without terrain context is misleading. A flat flood-prone hectare ≠ a hillside hectare.

## Migration phases (priority order)

### Phase 1 — DEM-derived terrain (live now: 1 region tested)

| Layer | Source | Paraguay extent | Method | Status |
|---|---|---|---|---|
| Hillshade backdrop | Copernicus GLO-30 | 7 regional rasters (~3-5 MB each) | Planetary Computer → Horn's method → JPEG | **building** (test running) |
| Hillshade 30m national tile | Copernicus GLO-30 | per-tile (7,912 tiles) | same | deferred |
| Color relief | Copernicus GLO-30 | 7 regional | color ramp by elevation | pending |
| DEM contours @ 25m | Copernicus GLO-30 | per-tile | gdal_contour | pending |
| DEM streams (D8) | Copernicus GLO-30 | per-tile | pysheds or richdem | pending |
| HAND (Height Above Nearest Drainage) | Copernicus GLO-30 + flow accumulation | per-tile | 5m floodplain, 5-15m riparian | pending |
| Slope raster | Copernicus GLO-30 | per-tile | numpy.gradient | pending |
| Aspect raster | Copernicus GLO-30 | per-tile | numpy.arctan2 | pending |

### Phase 2 — Land cover / forest

| Layer | Source | Status |
|---|---|---|
| MapBiomas 2023 | MapBiomas Paraguay | **already integrated** as `properties_heat_*` (deptos-level) |
| Hansen GFC loss 2000-2024 | Hansen/UMD/Google | pending (LQV has 1.78 MB geojson) |
| Hansen GFC gain | same | pending |
| Woodland merged (multi-source fusion) | MapBiomas + Hansen + OSM | pending |

### Phase 3 — Hydrology

| Layer | Source | Status |
|---|---|---|
| JRC Global Surface Water | EC JRC | pending (LQV has `lqv_jrc_waterbodies_10km.geojson`) |
| HydroSHEDS | WWF/USGS | pending |
| OSM water bodies | Geofabrik | **already integrated** as `water.geojson` (247 features) |
| Local quebradas | DEM-derived | pending |

### Phase 4 — Regulatory (Lucía's priority)

| Layer | Source | Notes |
|---|---|---|
| Municipal zoning (Asunción, CDE, Encarnación, etc.) | Municipal ordinances | Lucía is working on this with 2 architects |
| Construcción m² limits per zone | Municipal ordinances | "hasta cuántos m² podes construir" |
| Altura máxima permitida | Municipal ordinances | "hasta qué altura podes construir" |
| Setback requirements | Municipal ordinances | standard 3-5m per side |
| Uso de suelo permitido (residential/commercial/industrial) | Municipal Catastro | often maps to urban_zoning layer |
| Plan regulador urbano | Catastro Nacional + municipalities | rarely published digitally |

### Phase 5 — Other environmental

| Layer | Source | Status |
|---|---|---|
| SoilGrids 2.0 (texture, pH, organic carbon) | ISRIC | **not yet** but free API |
| NASA FIRMS fire alerts | NASA EOSDIS | pending |
| GBIF biodiversity | GBIF network | **already integrated** (200 species) |
| NASA POWER climate | NASA | **already integrated** (Asunción only) |
| Climate risk by depto | derived | **already integrated** (18 deptos) |
| Flood risk polygons | Catastro WFS | **already integrated** (5 zones) |

## What already migrated from LQV

| LQV data | Paraguay equivalent | Notes |
|---|---|---|
| hillshade_parcel.jpg (1.6 km²) | TBD — building | national extent |
| hillshade_10km.jpg (100 km²) | TBD | 1°×1° tiles |
| hillshade_escobar.jpg (50×36 km) | TBD | per depto |
| color_relief_10km.jpg | TBD | pending |
| dem_contours_10km.geojson | TBD | 25m elevation contours |
| dem_streams_10km.geojson | TBD | D8 flow accumulation |
| hand_10km.geojson | TBD | wetland classifier |
| ndvi_canopy_10km.geojson | TBD | canopy health |
| woodland_merged_10km.geojson | TBD | multi-source forest fusion |
| gbif CSV | gbif_paraguay.geojson | already done |
| osm_buildings_near.geojson | osm_buildings_*.geojson | 49,641 buildings in Asunción |
| osm_water_v2.geojson | water.geojson | 247 features |
| osm_roads_v2.geojson | roads.geojson | 14,835 features |
| mapbiomas_2023_10km.geojson | (deptos-level only) | needs scale-up |

## Effort estimates

| Phase | Wall time | Compute | Disk | API cost |
|---|---|---|---|---|
| 1 — DEM hillshade (national) | 4-6 hours | 30 GB RAM peak | 200 MB total | $0 (Copernicus free) |
| 2 — Forest cover | 2-3 hours | 10 GB RAM | 50 MB total | $0 (Hansen/MapBiomas free) |
| 3 — Hydrology | 1-2 hours | 10 GB RAM | 30 MB total | $0 (JRC, OSM) |
| 4 — Regulatory | ongoing (Lucía) | n/a | n/a | $0 (manual) |
| 5 — Other env | 1-2 hours | 5 GB RAM | 20 MB | $0 |

## Implementation notes

### Hillshade pipeline (Phase 1)

Already tested in `/root/paraguay-geodata/scripts/build_paraguay_hillshade.py`:
- Connect to Planetary Computer STAC API
- Fetch `cop-dem-glo-30` tiles covering Paraguay
- Compute Horn's method hillshade in memory
- Stack into 7 regional JPEGs (departamento-level) for the viewer
- Each region 3-5 MB JPEG + bounds JSON
- Loaded as `L.imageOverlay` with `opacity: 0.5`

### Strategy: tile-level vs regional

For a viewer at national zoom (z=5-7), showing 7,912 separate hillshades is wrong. Strategy:

- **z=5-9**: use 3-5 regional hillshades (one per macro-region: Oriental west, Oriental east, Chaco)
- **z=10-12**: still regional
- **z=13-15**: load priority-tile hillshades on demand (37 tiles × 80 KB each = 3 MB total)
- **z=16+**: use hillshade_parcel analog per-tile (7,912 tiles × 10 KB = 80 MB)

This matches the existing LQV approach (escobar-wide + parcel-scale).

### Regulatory data (Phase 4)

Lucía's role: collect municipal ordinances + provide per-zone construction rules.
Our role: ingest as JSON / GeoJSON, expose as overlay + popup detail.

Data model:
```json
{
  "zone_id": "asu-centro-residential-R2",
  "city": "Asunción",
  "category": "residential",
  "max_height_m": 15,
  "max_m2_construible": 200,
  "setback_m": 3,
  "allowed_use": ["vivienda", "comercio menor"],
  "forbidden_use": ["industrial", "gastronómico con extracción"],
  "ordinance_ref": "Ord. 246/94 art. 17",
  "last_updated": "2024-01-15"
}
```

This data goes into a `construction_zones.geojson` that the popup pulls when a property is clicked: "Estás en zona R2 — podés construir hasta 200 m² en 2 plantas, altura máx 15 m, retiro 3 m. Referencia: Ord. 246/94 art. 17."

## What we need from Lucía

Per her messages:

1. **Municipal ordinances** for Asunción (already has Catastro urban zoning), CDE, Encarnación, Pilar, etc.
2. **Per-zone construction limits** — m², altura, retiros, COS, FOT
3. **Special zones**: patrimonio histórico, riesgo ambiental, etc.
4. **List of architects/municipalities** who can validate the data

She suggested making the data downloadable from the site — we'll add a "Download regulatory data" section in the sidebar.

## Roadmap

- [x] Plan written (this doc)
- [ ] Test hillshade pipeline with Asunción 1°×1° (running now)
- [ ] Build 7 regional hillshades
- [ ] Integrate as L.imageOverlay layers
- [ ] Add contour lines (DEM-derived)
- [ ] Add HAND wetland classifier
- [ ] Migrate Hansen GFC + MapBiomas to national scale
- [ ] Receive regulatory data from Lucía
- [ ] Build per-property regulatory popup summary
- [ ] Add "Download" page for regulatory data

## References

- [LQV hillshade pipeline](https://github.com/Ai-Whisperers/la-quebrada-viva/tree/main/scripts)
- [Planetary Computer COP-30 docs](https://planetarycomputer.microsoft.com/dataset/cop-30)
- [HORN (1981) Hillshade algorithm](https://ieeexplore.ieee.org/document/1456186)
- [HAND methodology](https://www.mdpi.com/2072-4292/5/8/4147)
- [Catastro Nacional WFS](https://www.catastro.gov.py/geoserver)