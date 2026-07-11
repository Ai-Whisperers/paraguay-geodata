# Paraguay Geodata Platform — HONEST STATUS

**Live:** https://geodata.paragu-ai.com/ · **Repo:** https://github.com/Ai-Whisperers/paraguay-geodata
**HEAD:** tracked in deploy-meta.json · **Last commit:** see `git log -1`

## What this actually is

A free, open, viewer for Paraguay real-estate + cadastral + environmental data. ~10,898 listings, 21 toggleable layers, 8,238 Catastro features, mobile-responsive.

## What this is NOT (yet)

- ❌ **Not real-time.** Data is a static snapshot. No automatic refresh yet.
- ❌ **Not a B2B SaaS.** No API keys, no auth, no saved searches.
- ❌ **Not a mobile app.** It's a PWA-installable responsive web app.
- ❌ **Not production-grade ML.** The fair-price model has R² ≈ 0.017 (basically noise — it's a UI decoration, not a real valuation).

## Endpoints (15 files, ~50 MB)

| File | Size | Status | Purpose |
|---|---|---|---|
| `index.html` | ~85 KB | ✓ live | Main viewer |
| `manifest.webmanifest` | 1 KB | ✓ live | PWA install |
| `properties_latest.geojson` | 15 MB | ✓ live | 10,898 listings (PII scrubbed) |
| `roads.geojson` | 5.6 MB | ✓ live | 14,835 OSM roads |
| `buildings_asuncion.geojson` | 13.7 MB | ✓ live | 50K OSM building footprints |
| `water.geojson` | 2.5 MB | ✓ live | OSM water bodies |
| `gbif_paraguay.geojson` | 94 KB | ✓ live | 200 species |
| `tile_index.json` | 3.6 MB | ✓ live | 7,912 tiles |
| `priority_tiles.json` | 17 KB | ✓ live | 37 urban-anchor tiles |
| `bcp_snapshot.json` | 2 KB | ✓ live | BCP macro snapshot |
| `nasa_power_asuncion.json` | 1 KB | ✓ live | NASA POWER climate |
| `inbio_zafra_2025_2026.json` | 4 KB | ✓ live | INBIO crop area |
| `admin/catastro_dpto.geojson` | 35 KB | ✓ live | **NEW** 18 deptos (Catastro WFS) |
| `admin/catastro_dist.geojson` | 296 KB | ✓ live | **NEW** 268 distritos (Catastro WFS) |
| `admin/catastro_parcels_sample.geojson` | 4.4 MB | ✓ live | **NEW** 7,500 parcelas (Catastro WFS) |
| `admin/catastro_urba.geojson` | 800 KB | ✓ live | **NEW** 470 urbanizaciones (Catastro WFS) |
| `ml/fair_price_model.json` | 6 KB | ✓ live | **NEW** ML fair-price (UI only, R²≈0.017) |

## 21 toggleable layers (17 default-on, 4 opt-in)

| Group | Layer | Active | Loaded |
|---|---|---|---|
| Grid | tile_fabric (7,912 cells) | ✓ | ✓ |
| Grid | priority_tiles (37) | ✓ | ✓ |
| Admin OSM | departamentos_py (18) | ✓ | ✓ |
| Admin OSM | distritos_py (268) | hidden | ✓ |
| Admin OSM | barrios_py (1,278) | hidden | ✓ |
| Admin Catastro | catastro_dpto (18) | hidden | ✓ |
| Admin Catastro | catastro_dist (268) | hidden | ✓ |
| Admin Catastro | catastro_parcels (7,500) | hidden | ✓ |
| Admin Catastro | catastro_urba (470) | hidden | ✓ |
| Agriculture | inbio_soja | ✓ | ✓ |
| Agriculture | inbio_arroz | hidden | ✓ |
| Agriculture | inbio_maiz | hidden | ✓ |
| Real estate | properties_infocasas (10,898) | ✓ | ✓ |
| Real estate | properties_heat_pha | hidden | ✓ |
| Real estate | properties_heat_area | hidden | ✓ |
| Urban | osm_roads (14,835) | hidden | ✓ |
| Urban | osm_buildings (50K) | hidden | ✓ |
| Urban | osm_water (247) | hidden | ✓ |
| Urban | anchor_circles (17) | hidden | ✓ |
| Biodiversity | gbif_animalia (200) | hidden | ✓ |
| Biodiversity | gbif_plantae (200) | hidden | ✓ |

## Features — honestly

| Feature | Works | Notes |
|---|---|---|
| Map (Leaflet) | ✓ | Full Paraguay, OSM tiles |
| 21 toggleable layers | ✓ | All loaded + toggleable |
| Property markers (clustered) | ✓ | Grid-based clustering at zoom <11 |
| Property popups (image + price) | ✓ | Image gallery + comparables |
| Photon geocoder | ✓ | Real address search (Calle Palma, Asunción, etc.) |
| Mobile drawer (sidebar) | ✓ | Hidden by default, hamburger menu |
| Mobile filter sheet | ✓ | Bottom sheet with 6 filters |
| Mobile touch targets ≥44px | ✓ | Apple HIG-compliant |
| WCAG 2.2 AA (skip-link, focus) | partial | Surface-level; no axe-core audit |
| prefers-reduced-motion | ✓ | CSS media query |
| prefers-contrast (more) | ✓ | CSS media query |
| PII scrubbed | ✓ | 10,898 listings, agent phones/emails → null |
| Market signals (auto) | ✓ | Live compute: 10,898 listings, median $90K |
| Share view button | ✓ | URL with lat/lon/z/layers |
| Embed widget (?embed=1) | ✓ | Hides sidebar |
| Geolocation | ✓ | One-click find me |
| URL hash sync | ✓ | ?lat=&lon=&z=&layers= |
| CSV export | ✓ | 16 columns, current snapshot |
| Filter by price/type/beds/area | ✓ | Live filter, re-cluster on apply |
| Fair-price ML | ⚠️ | R² ≈ 0.017; UI decoration only |
| Yield calculator | ✓ | Gross/net yield, payback years |
| Lang switcher (es/en/gn) | partial | EN/ES work, GN only 5 keys |
| PWA installable | partial | Manifest exists, no service worker yet |
| Auto data refresh | ❌ | Manual only |

## Known issues / what's NOT done

- **No auto-refresh** — data is whatever the last scrape produced. Will go stale.
- **No user accounts / saved searches** — can't return to a query
- **No service worker** — installable PWA but no offline mode
- **GN (Guaraní)** — only 5 keys translated, not usable as primary language
- **No charts library** — all stats are text, not graphs
- **Mobile breakpoint at 880px** — tablet users (768-880px) get the mobile drawer
- **10,898 properties' geo accuracy** — relies on source data; ~529 have unknown depto
- **5,649 properties with PII scrubbing** — confirmed agent phones null, no leak check on emails beyond @-pattern
- **No tests** — ad-hoc shell scripts only
- **No CI** — manual `wrangler deploy`
- **No monitoring** — no uptime check, no error reporting

## Sources

- **Properties:** infocasas (UY aggregator with PY coverage), TuLugar, Clasipar — scraped ethically
- **OSM:** Geofabrik Paraguay extract
- **Agriculture:** INBIO zafra 2025-2026
- **Biodiversity:** GBIF (200 species)
- **Macro:** BCP Feb 2026, NASA POWER (Asunción)
- **Cadastre:** Catastro Nacional WFS (catastro.gov.py/geoserver)
- **Geocoder:** Photon (komoot.io)

## Licenses

- Data: Catastro (Ley 5282/14 open), OSM (ODbL), GBIF (CC0/CC-BY), INBIO/BCP (public)
- Code: MIT
- PII: scrubbed before publish

## Maintainers

- Open contribution via PR
- GitHub: https://github.com/Ai-Whisperers/paraguay-geodata

## How to extend

See `/docs/PLAN.md` for the 312-item roadmap organized into 7 phases.