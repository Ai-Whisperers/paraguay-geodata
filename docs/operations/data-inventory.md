# Master Data Inventory — Paraguay Geodata

The single page that answers "what can the map show today?". Update whenever a new layer is integrated.

**Last updated**: 2026-07-10 (post-Phase 0.5 expansion)

---

## Live layers (Phase 0.5 commit)

These will be available in the viewer once `tools/fetch_tile.py` wires them in. Phase 1 ships these; everything else is queued.

### Admin boundaries (INE)

| Layer | Source | Geometry | Cost | Status |
|---|---|---|---|---|
| Departamentos (17) | INE Cartografía 2012 | Polygon | Free | Phase 1 |
| Distritos (~262) | INE Cartografía 2012 | Polygon | Free | Phase 1 |
| Barrios / Localidades | INE Cartografía 2012 | Polygon | Free | Phase 1 |
| Manzanas | INE Cartografía 2012 | Polygon | Free | Phase 1 |
| Vías principales | INE | LineString | Free | Phase 1 |
| Hidrografía | INE | LineString | Free | Phase 1 |
| Comunidades indígenas | INE | Polygon | Free | Phase 1 |
| Locales Salud | INE | Point | Free | Phase 1 |
| Locales Policial | INE | Point | Free | Phase 1 |
| Locales Educación | INE | Point | Free | Phase 1 |

### Satellite + topography

| Layer | Source | Format | Cost | Status |
|---|---|---|---|---|
| DEM (Copernicus GLO-30) | ESA / Planetary Computer | COG | Free | Phase 1 |
| Sentinel-2 RGB + NDVI | ESA / Planetary Computer | COG-JP2 | Free | Phase 1 |
| Esri HD (z=17, z=18) | ArcGIS REST | PNG tiles | Free | Phase 1 |
| OSM 10 km (8 layers) | OSM Overpass | GeoJSON | Free | Phase 1 |
| MapBiomas Paraguay | MapBiomas | GeoTIFF | Free (CC BY 4.0) | Phase 1 |
| Hansen GFC | UMD / Google | GeoTIFF | Free (CC BY 4.0) | Phase 1 |
| JRC Surface Water | EC JRC | GeoTIFF | Free | Phase 1 |
| HydroSHEDS | WWF / USGS | GeoTIFF + shp | Free (CC BY 4.0) | Phase 1 |
| NASA FIRMS | NASA EOSDIS | CSV daily | Free (API key) | Phase 1 |
| GBIF | GBIF | JSON | Free | Phase 1 |

### Derived (per-tile)

| Layer | From | Status |
|---|---|---|
| Streams | DEM (pysheds) | Phase 1 |
| Cerros | DEM (closed-contour algorithm) | Phase 1 |
| Contours | DEM | Phase 1 |
| Slope | DEM | Phase 1 |
| Aspect | DEM | Phase 1 |
| Hillshade (multi-azimuth) | DEM | Phase 1 |
| Color-relief | DEM | Phase 1 |
| HAND (Height Above Nearest Drainage) | DEM + streams | Phase 1 |
| NDVI canopy | Sentinel-2 | Phase 1 |
| NDVI density → tree positions | NDVI raster | Phase 1 |

### Properties + price (Phase 2)

| Layer | Source | Cost | Status |
|---|---|---|---|
| Active listings | infocasas, propiedades, baiker | Free (scraped) | Phase 2 |
| Escritura anchors | operator-supplied | Free | Phase 2 |
| Kriged price surface | listings + anchors | Free | Phase 2 |
| Price hexagons | kriging output | Free | Phase 2 |
| Listing–escritura match | distance + price band | Free | Phase 2 |

### Commercial (Phase 1.5+)

| Layer | Source | Cost | Status |
|---|---|---|---|
| DNCP tender calls | DNCP API V3 | Free (API key) | Phase 1.5 |
| DNCP awards | DNCP API V3 | Free (API key) | Phase 1.5 |
| DNCP suppliers | DNCP API V3 | Free (API key) | Phase 1.5 |
| MIC maquila registry | MIC | TBD | Phase 2 |
| SET RUC lookup | SET | Free | Phase 2 |

### Agriculture (Phase 1.5+)

| Layer | Source | Cost | Status |
|---|---|---|---|
| INBIO crop area | INBIO | Free | Phase 1.5 |
| INBIO yield per ha | INBIO | Free | Phase 1.5 |
| INFONA forest plantation | INFONA | Free | Phase 2 |
| INFONA harvest permits | INFONA | Free | Phase 2 |
| SENAVE phytosanitary | SENAVE | Free | Phase 2.5 |
| SENACSA cattle density | SENACSA | Free | Phase 2 |
| SoilGrids lookup | ISRIC | Free (CC BY 4.0) | Phase 1 |

### Infrastructure (Phase 1.5+)

| Layer | Source | Cost | Status |
|---|---|---|---|
| ANDE power grid | ANDE | Free | Phase 2 |
| ANDE electrification % | ANDE | Free | Phase 2 |
| ESSAP water coverage | ESSAP | Free | Phase 2 |
| COPACO fiber backbone | COPACO | Free | Phase 2.5 |
| MOPC routes | MOPC + OSM | Free | Phase 1.5 |
| Distance-to-power | derived | Free | Phase 1 |
| Distance-to-water | derived | Free | Phase 1 |
| Fuel stations | Petropar + OSM | Free | Phase 1.5 |
| Distance-to-school | derived | Free | Phase 1 |
| Distance-to-hospital | derived | Free | Phase 1 |
| Distance-to-police-station | derived | Free | Phase 1 |

### Environment (Phase 1+)

| Layer | Source | Cost | Status |
|---|---|---|---|
| FIRMS active fires | NASA | Free | Phase 1 |
| Hansen loss/gain | UMD | Free | Phase 1 |
| JRC water occurrence | JRC | Free | Phase 1 |
| MADES air quality | MADES | TBD | Phase 1.5 |
| CHIRPS rainfall | CHIRPS | Free | Phase 2 |
| ERA5 soil moisture | ECMWF CDS | Free (account) | Phase 2.5 |
| CMIP6 climate projections | various | Free | Phase 3 |
| AON catastrophe risk | AON commercial | Paid | Phase 3 (TBD) |

### Socioeconomic (Phase 1.5+)

| Layer | Source | Cost | Status |
|---|---|---|---|
| IPM poverty | INE | Free | Phase 1.5 |
| EPH per-capita income | INE | Free | Phase 2 |
| Banking density | BCP | Free | Phase 2 |
| Policia Nacional crime | Policia | Free | Phase 2.5 |
| AHK / UIP foreign investment | Chambers | Free | Phase 2.5 |
| Population projection 2050 | INE | Free | Phase 1.5 |

### Communications (Phase 3)

| Layer | Source | Cost | Status |
|---|---|---|---|
| Tigo/Personal/Claro 4G/5G | Mobile operators | TBD | Phase 3 |
| OpenSignal crowdsourced | OpenSignal | Paid | Phase 3 (TBD) |

### 3D / advanced (Phase 3)

| Layer | Source | Cost | Status |
|---|---|---|---|
| Cesium globe (national) | derived | Free (CDN) | Phase 3 |
| Per-tile Three.js planner | derived | Free | Phase 3 |
| Gaussian splat (key sites) | capture + Nerfstudio | Paid (compute) | Phase 3 (TBD) |

---

## Total layer count

| Phase | Layers added | Cumulative |
|---|---|---|
| 0 (shipped) | 0 (only stubs) | 0 |
| 1 (planned) | +24 (satellite + admin + env) | 24 |
| 1.5 | +18 (commercial + socio + dist-to-X) | 42 |
| 2 | +12 (listings + price + agro + infra) | 54 |
| 2.5 | +8 (rural overlays) | 62 |
| 3 | +8 (3D + climate) | 70 |

**70 distinct toggleable layers at full coverage.** Each phase adds 8-24.

---

## Cost summary

| Tier | Layers | Cost |
|---|---|---|
| Free + open | 60+ | $0 |
| Free with API key | 5 (FIRMS, DNCP, BC, etc.) | $0 (just registration) |
| Paid commercial | 2 (AON, OpenSignal) | $50-200/mo |
| Capture + compute | 2 (splat + UE5 walkthrough) | $200-1000 one-time |

**Floor**: $0/mo for the core viewer. **Recommended add-on**: $50/mo for AON catastrophe data when the user wants insurance-grade risk overlay.

---

## Open questions for the operator

| Question | Default | Block |
|---|---|---|
| Custom domain for deploy | TBD | Phase 1 |
| Whether to deploy national globe first or per-tile drilldown | per-tile first | Phase 1 |
| Whether to include AON paid catastrophe overlay | NO (Phase 3 backlog) | Phase 3 |
| Whether to do 3D splats in key metros | YES — Asunción, CDE, Encarnación | Phase 3 |
| Whether to integrate listing-agency RUC validation | YES — free | Phase 2 |

---

## How this doc gets used

- This is the **gate** before "do all of this" goes into a phase plan.
- Every commit that changes a layer (adds, retires, refreshes cadence) updates the relevant table here.
- The "Total layer count" table is the **stakeholder-facing metric**: how complete is the platform?
- New data sources start as `Phase X.TBD` and graduate to `Phase X.0` when their tool ships.

---

## See also

- `docs/sources/*.md` — per-category deep dive
- `docs/operations/national-tile-fabric.md` — phased rollout
- `docs/operations/properties-pipeline.md` — listings
- `docs/operations/price-model.md` — price surface
- `docs/ethics/scraper-policy.md` — scraper gate