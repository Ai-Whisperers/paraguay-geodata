# Paraguay Geodata

[![Tests](https://img.shields.io/badge/tests-339_passing-brightgreen)](#)
[![Coverage](https://img.shields.io/badge/coverage-25%25-yellow)](#)
[![Live](https://img.shields.io/badge/live-geodata.paragu--ai.com-blue)](https://geodata.paragu-ai.com)

National-scale Paraguay satellite + geospatial data platform.

Forked from [`Ai-Whisperers/la-quebrada-viva`](https://github.com/Ai-Whisperers/la-quebrada-viva) — the same architecture that powers the [LQV walkthrough viewer](https://lqv-walkthrough.pages.dev/mapa.html) (62-ha property in Escobar, Paraguarí), extended to country scale.

## What this is

A complete, reproducible stack for **every square kilometre of Paraguay** at the same depth of data we built for one 10×10 km box in Paraguarí:

- **DEM + topography** — Copernicus GLO-30, derived streams, contours, cerros, slope, aspect, hillshade
- **Satellite imagery** — Esri HD at LOD2/LOD3, Sentinel-2 L2A, NDVI canopy
- **Land cover + change** — MapBiomas Paraguay, Hansen GFC loss/gain
- **Hydrology** — JRC Global Surface Water, HydroSHEDS, HAND
- **Biodiversity** — GBIF Paraguay slice, NASA FIRMS fire hotspots
- **Properties on sale** — listings from infocasas / propiedades.com.py / baiker, cross-referenced against catastro/escritura anchors
- **Hedonic price surfaces** — per-departamento $/ha raster, kriged from listings + escrituras

All accessible through a single Leaflet/MapLibre viewer (`/mapa.html`) that scales from a single property to a national coverage heatmap.

## Stack at a glance

| Layer | Tech | Cost |
|---|---|---|
| Tile storage (raster-heavy: DEM, Esri HD, Hansen, MapBiomas) | Cloudflare R2 | Free tier covers ~100-500 GB/year |
| Static frontend deploy | Cloudflare Pages | Free (limit 25 MiB per file — heavy rasters in R2) |
| Listings scrape + dedup | Python + jQuery-equivalent HTML parser | $0 + rate-limited crawlers |
| Hedonic price raster | kriging over listings + escrituras | Compute-only |
| Data license | MIT (code) + CC0 (data) | Same as LQV |

## Architecture (one-line)

```
1000× Paraguay bbox tiles (10×10 km)  →  data/tiles/<lon>_<lat>/  →
  per-tile: DEM + Esri + OSM + S2 + MapBiomas + Hansen + JRC + FIRMS  →
  national Cesium globe + per-tile Leaflet viewer at lqv-walkthrough-style  →
  properties + price overlay as additional toggleable layers
```

See `ARCHITECTURE.md` for full design + `docs/operations/national-tile-fabric.md` for the phased rollout.

## Phased delivery

| Phase | Deliverable | Status |
|---|---|---|
| **Phase 0** | Repo + 4-doc skeleton + tile index + ethics gate | 🟡 In progress (this commit) |
| **Phase 1** | Satellite + topographic coverage over the grid (week 2-3) | ⏳ Queued |
| **Phase 2** | Properties + price surface (week 4) | ⏳ Queued |
| **Phase 3** | National Cesium globe + per-tile 3D world | ⏳ Queued |

See `STATUS.md` for live state + `docs/operations/national-tile-fabric.md` for the full plan.

## Origin & lineage

| Repo | Visibility | Status | What's there |
|---|---|---|---|
| `Ai-Whisperers/la-quebrada-viva` | private | byte-frozen at escritura 2026-06-27 | The 62-ha reference impl + the technique |
| `Ai-Whisperers/paraguay-geodata` (this) | private | starting | National-scale extension |

LQV is the **executable reference**. Every tool in `tools/` here originated from LQV's `tools/` (e.g. `build_peaks_geojson.py`, `build_slope_aspect.py`, `lqv_fetch_esri_hd.py`) — extracted and parameterised for national tiling. The lqv-bundle skill owns the **technique**; this repo owns the **scale**.

## License

- **Code**: MIT (see `LICENSE`)
- **Data**: CC0 (no attribution required) for the derivative GeoJSON we publish
- **Source data**: each upstream provider's license is preserved per `docs/sources/*.md` + `CREDITS.md`
