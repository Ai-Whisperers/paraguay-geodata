# Credits — Paraguay Geodata

## Origin

Forked from `Ai-Whisperers/la-quebrada-viva` (La Quebrada Viva — 62-ha property in
Escobar, Paraguarí). The LQV repo provided the **technique** — the
proved-at-scale approach to fusing DEM + satellite + OSM + land-cover into a
single interactive viewer at 10×10 km. This repo applies that technique
across the whole country.

## Tools (Py / Bash / JS)

| Tool | Role | Source |
|---|---|---|
| `tools/national_tile_index.py` | Paraguay bbox 10×10 km fabric index | new in this repo |
| `tools/fetch_tile.py` | Per-tile DEM + Esri + OSM + S2 + MapBiomas + Hansen + JRC orchestrator | derived from `lqv/tools/lqv_fetch_*` family |
| `tools/build_peaks_geojson.py` | DEM-derived cerros algorithm | extracted from LQV `tools/build_peaks_geojson.py` |
| `tools/build_slope_aspect.py` | Slope / aspect / hillshade generator | extracted from LQV `tools/build_slope_aspect.py` |
| `tools/fetch_properties.py` | Listings scraper (infocasas / propiedades.com.py / baiker) | new in this repo |
| `tools/build_price_surface.py` | Hedonic kriging → $/ha raster per departamento | new in this repo |

## Upstream Data Providers

| Data | Provider | License | URL |
|---|---|---|---|
| DEM (Copernicus GLO-30) | ESA / Copernicus | Free + open | `https://planetarycomputer.microsoft.com/dataset/cop-30` |
| DEM (NASADEM, fallback) | NASA / JPL | Public domain | `https://planetarycomputer.microsoft.com/dataset/nasadem` |
| Esri World Imagery | Esri / ArcGIS REST | Free for tiles ≤ z=19 | `https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer` |
| Sentinel-2 L2A | ESA Copernicus via Element84 STAC + Microsoft Planetary Computer | Free + open | `https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a` |
| OpenStreetMap | OSM contributors | ODbL | `https://overpass-api.de/api/interpreter` |
| MapBiomas Paraguay | MapBiomas / SOS Mata Atlântica + Guyra Paraguay | CC BY 4.0 | `https://plataforma.mapbiomas.org/` |
| Hansen GFC | Hansen/UMD/Google | CC BY 4.0 | `https://storage.googleapis.com/umd_hansen_dl4/` |
| JRC Global Surface Water | EC JRC | Free + open | `https://global-surface-water.appspot.com/download` |
| HydroSHEDS | WWF / USGS | CC BY 4.0 | `https://www.hydrosheds.org/` |
| NASA FIRMS | NASA EOSDIS | Public domain | `https://firms.modaps.eosdis.nasa.gov/` |
| GBIF | GBIF network | varies (CC0 / CC BY / CC BY-NC) | `https://api.gbif.org/v1/` |
| SoilGrids 2.0 | ISRIC | CC BY 4.0 | `https://rest.isric.org/soilgrids/v2.0/` |
| SNC padrones | Paraguay Servicio Nacional de Catastro | Public records | `https://www.catastro.gov.py/` |
| Listings (infocasas) | InfoCasas Paraguay | Provided by portal — see `docs/ethics/scraper-policy.md` | `https://www.infocasas.com.py/` |
| Listings (propiedades.com.py) | Propiedades.com.py | Provided by portal — see `docs/ethics/scraper-policy.md` | `https://www.propiedades.com.py/` |
| Listings (baiker) | Baiker | Provided by portal — see `docs/ethics/scraper-policy.md` | `https://www.baiker.com/` |

## Cloud Infrastructure

| Service | Use | Cost |
|---|---|---|
| Cloudflare Pages | Static front-end deploy (HTML, JS, small GeoJSONs) | Free (with limits) |
| Cloudflare R2 | Heavy raster storage (DEM, Esri HD, S2, Hansen) | Free tier covers ~100-500 GB/year |
| Hermes cron (orchestrator) | Nightly fetch + rebuild cron jobs | $0 |

## Humans

- **Operator**: Iván (Ai-Whisperers founder) — decisions + direction
- **Erebus** (AI workforce lead) — repo structure, doc skeleton, tool extraction
- **Prior LQV authors**: Nyx + the lqv-bundle codeowners — the technique

## AI Skills Consumed

- `lqv-bundle` — project-instance state machine
- `satellite-to-blender-pipeline` — class-level technique (3DGS, UE5, capture)
- `paraguay-open-data-fetch` — source catalogue
- `ethical-web-scraping-decision` — scraper policy gate
- `cloudflare-pages-deployment` — deploy health checks

## Full Licence Terms

- Code: see `LICENSE` (MIT).
- Derivative data we publish: CC0.
- Underlying sources: each retains its own license per the table above.
- Listings: see `docs/ethics/scraper-policy.md` for the snapshot-license guardrails.

---

**Last updated**: 2026-07-10
