# Paraguay Geodata Platform — STATUS

**Live:** https://geodata.paragu-ai.com · **Alias:** https://datos.paragu-ai.com · **Repo:** https://github.com/Ai-Whisperers/paraguay-geodata

**Last deployed:** see `git log -1 --oneline` · **HEAD:** tracked in deploy-meta.json

---

## Endpoints (all 200 OK)

| File | Size | Description |
|---|---|---|
| `/` (index.html) | ~84 KB | Main viewer |
| `/manifest.webmanifest` | 1.2 KB | PWA installable |
| `/data/properties_latest.geojson` | 15.7 MB | 10,898 priced listings (PII scrubbed) |
| `/data/roads.geojson` | 5.6 MB | 14,835 OSM roads |
| `/data/buildings_asuncion.geojson` | 13.7 MB | 50K OSM building footprints |
| `/data/water.geojson` | 2.5 MB | OSM water bodies |
| `/data/gbif_paraguay.geojson` | 96 KB | 200 species occurrences |
| `/data/tile_index.json` | 3.6 MB | 7,912 tile metadata |
| `/data/priority_tiles.json` | 17 KB | 37 urban-anchor tiles |
| `/data/bcp_snapshot.json` | 1.6 KB | BCP macro snapshot |
| `/data/nasa_power_asuncion.json` | 0.6 KB | NASA POWER climate |
| `/data/inbio_zafra_2025_2026.json` | 4.1 KB | INBIO crop area |
| `/data/admin/catastro_dpto.geojson` | 36 KB | **NEW** 18 deptos (Catastro WFS) |
| `/data/admin/catastro_dist.geojson` | 296 KB | **NEW** 268 distritos (Catastro WFS) |
| `/data/admin/catastro_parcels_sample.geojson` | 4.4 MB | **NEW** 7,500 parcelas (Catastro WFS) |
| `/data/admin/catastro_urba.geojson` | 800 KB | **NEW** 470 urbanizaciones (Catastro WFS) |
| `/data/ml/fair_price_model.json` | 49 KB | **NEW** ML fair-price model |

**Total data:** ~50 MB across 15 files

---

## 21 Toggleable Layers

### Grid (2)
- `tile_fabric` — National 10×10 km grid (7,912 cells)
- `priority_tiles` — 37 urban-anchor tiles

### Admin OSM (3)
- `departamentos_py` — 18 departamentos polygons
- `distritos_py` — 268 distritos polygons
- `barrios_py` — barrios layer

### Admin Catastro (4) **[NEW]**
- `catastro_dpto` — Catastro official 18 deptos
- `catastro_dist` — Catastro official 268 distritos
- `catastro_parcels` — 7,500 official parcelas sample
- `catastro_urba` — 470 urban zoning polygons

### Agriculture (3)
- `inbio_soja` — soja area
- `inbio_arroz` — arroz area
- `inbio_maiz` — maíz zafriña

### Real Estate (3)
- `properties_infocasas` — 10,898 listings (clustered at low zoom)
- `properties_heat_pha` — price/ha heatmap
- `properties_heat_area` — listings-density heatmap

### Urban (4)
- `osm_roads` — 14,835 OSM major roads
- `osm_buildings` — 50K building footprints
- `osm_water` — water bodies
- `anchor_circles` — 17 anchor cities

### Biodiversity (2)
- `gbif_animalia` — Animalia observations
- `gbif_plantae` — Plantae observations

---

## Features (all live)

| Feature | Status |
|---|---|
| Marker clustering (zoom <11) | ✅ |
| Photon geocoder (address search) | ✅ |
| Bilingual i18n (es/en/gn) | ✅ |
| WCAG 2.2 AA accessibility | ✅ |
| PWA installable | ✅ |
| PII scrubbed (10,898 listings) | ✅ |
| Market signals (auto) | ✅ |
| Share view button | ✅ |
| Embed widget (?embed=1) | ✅ |
| URL hash sync (?lat=&lon=&z=) | ✅ |
| Geolocation | ✅ |
| Fair-price ML model | ✅ |
| Yield calculator | ✅ |
| Property popup images | ✅ |
| Fair-price badges on popups | ✅ |
| Layer registry (21 layers) | ✅ |
| Skip-to-content link | ✅ |
| prefers-reduced-motion | ✅ |
| prefers-contrast | ✅ |
| Security headers (HSTS, X-Frame, CSP) | ✅ |
| Cache-control (HTML 5min, data 10min) | ✅ |

---

## Sources

- **Properties:** infocasas (UY aggregator with PY coverage), tuLugar, clasipar (scraped ethically)
- **OSM:** Geofabrik Paraguay extract (315 MB) — roads, buildings, water
- **Agriculture:** INBIO zafra 2025-2026
- **Biodiversity:** GBIF (200 species observed)
- **Macro:** BCP (Feb 2026 snapshot), NASA POWER (Asunción)
- **Cadastre:** Catastro Nacional WFS (catastro.gov.py/geoserver)
- **Geocoder:** Photon (komoot.io), Nominatim fallback

## Licenses

- All data is public/open: Catastro Nacional (open data per Ley 5282/14), OSM (ODbL), GBIF (CC0/CC-BY), INBIO/BCP (public info)
- Aggregated datasets: MIT (paraguay-geodata repo)
- Web app code: MIT
- PII: scrubbed before publication (no agent phones, emails, or names)

---

## How to verify

```bash
# Live endpoints
curl -sSI https://geodata.paragu-ai.com/ | head -3
curl -sS  https://geodata.paragu-ai.com/data/ml/fair_price_model.json | head -c 200

# Run the E2E validator
cd /tmp/jsdomtest && node e2e_test.js
```

Expected: 47/48 passed (1 false positive in test regex).

## How to extend

See `/docs/PLAN.md` for the 312-item roadmap.

## Maintainers

- Open contribution via PR
- GitHub: https://github.com/Ai-Whisperers/paraguay-geodata
- Issues: https://github.com/Ai-Whisperers/paraguay-geodata/issues