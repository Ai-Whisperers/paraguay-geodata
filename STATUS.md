# Paraguay Geodata Platform — HONEST STATUS

**Live:** https://geodata.paragu-ai.com/ · **Repo:** https://github.com/Ai-Whisperers/paraguay-geodata
**HEAD:** tracked in deploy-meta.json · **Last commit:** see `git log -1`

## What this actually is

A free, open, viewer for Paraguay real-estate + cadastral + environmental data. ~10,898 listings, 21 toggleable layers, 8,238 Catastro features, mobile-responsive, lazy-loads 25 MB of geojson on demand.

## What this is NOT (yet)

- ❌ **Not real-time.** Data is a static snapshot. No automatic refresh yet.
- ❌ **Not a B2B SaaS.** No API keys, no auth, no saved searches (localStorage saved-listings work).
- ❌ **Not a mobile app.** It's a PWA-installable responsive web app.
- ❌ **Not production-grade ML.** The fair-price model has R² ≈ 0.017 (basically noise — it's a UI decoration, not a real valuation).

## Endpoints (15 files, ~50 MB)

| File | Size | Status | Purpose |
|---|---|---|---|
| `index.html` | ~85 KB | ✓ live | Main viewer |
| `manifest.webmanifest` | 1 KB | ✓ live | PWA install |
| `properties_latest.geojson` | 14 MB | ✓ live | 10,898 listings (PII scrubbed) |
| `roads.geojson` | 5.6 MB | ✓ lazy | 14,835 OSM roads |
| `buildings_asuncion.geojson` | 13 MB | ✓ lazy | 49,641 OSM building footprints |
| `water.geojson` | 2.5 MB | ✓ lazy | OSM water bodies |
| `gbif_paraguay.geojson` | 94 KB | ✓ live | 200 species |
| `tile_index.json` | 3.6 MB | ✓ live | 7,912 tiles |
| `priority_tiles.json` | 17 KB | ✓ live | 37 urban-anchor tiles |
| `bcp_snapshot.json` | 2 KB | ✓ live | BCP macro snapshot |
| `nasa_power_asuncion.json` | 1 KB | ✓ live | NASA POWER climate + 12-month breakdown |
| `inbio_zafra_2025_2026.json` | 4 KB | ✓ live | INBIO crop area |
| `admin/catastro_dpto.geojson` | 35 KB | ✓ lazy | 18 deptos (Catastro WFS) |
| `admin/catastro_dist.geojson` | 296 KB | ✓ lazy | 268 distritos (Catastro WFS) |
| `admin/catastro_parcels_sample.geojson` | 4.4 MB | ✓ lazy | 7,500 parcelas (Catastro WFS) |
| `admin/catastro_urba.geojson` | 800 KB | ✓ lazy | 470 urbanizaciones (Catastro WFS) |
| `ml/fair_price_model.json` | 6 KB | ✓ live | ML fair-price (UI only, R²≈0.017) |

## 21 toggleable layers (17 default-on, 4 opt-in)

| Group | Layer | Active | Loaded |
|---|---|---|---|
| Grid | tile_fabric (7,912 cells) | ✓ | ✓ |
| Grid | priority_tiles (37) | ✓ | ✓ |
| Admin OSM | departamentos_py (18) | ✓ | ✓ |
| Admin OSM | distritos_py (268) | hidden | lazy |
| Admin OSM | barrios_py (236) | hidden | lazy |
| Admin Catastro | catastro_dpto (18) | hidden | lazy |
| Admin Catastro | catastro_dist (268) | hidden | lazy |
| Admin Catastro | catastro_parcels (7,500) | hidden | lazy |
| Admin Catastro | catastro_urba (470) | hidden | lazy |
| Agriculture | inbio_soja | ✓ | ✓ |
| Agriculture | inbio_arroz | hidden | ✓ |
| Agriculture | inbio_maiz | hidden | ✓ |
| Real estate | properties_sale (8,219) | ✓ | ✓ |
| Real estate | properties_rent | hidden | ✓ |
| Real estate | properties_short | hidden | ✓ |
| Real estate | properties_house | hidden | ✓ |
| Real estate | properties_apartment | hidden | ✓ |
| Real estate | properties_land | hidden | ✓ |
| Real estate | properties_commercial | hidden | ✓ |
| Real estate | properties_heat_pha | hidden | lazy |
| Real estate | properties_heat_area | hidden | lazy |
| Urban | osm_roads (14,835) | hidden | lazy |
| Urban | osm_buildings (49,641) | hidden | lazy |
| Urban | osm_water (247) | hidden | lazy |
| Urban | anchor_circles (20 cities) | hidden | lazy |
| Biodiversity | gbif_animalia (200) | hidden | lazy |
| Biodiversity | gbif_plantae (200) | hidden | lazy |

## Features — honestly

| Feature | Works | Notes |
|---|---|---|
| Map (Leaflet) | ✓ | Full Paraguay, OSM tiles, 8 attribution options |
| 21 toggleable layers | ✓ | All lazy-loaded on first activation |
| Property markers (clustered) | ✓ | Grid-based at zoom <11, individual at zoom >=11 |
| Property markers (price-scaled) | ✓ | Log-scale radius 3-14 px by price |
| Property popups (image + price) | ✓ | Image gallery + comparables + Google Maps deep link |
| Saved listings (localStorage) | ✓ | ☆ Save, ★ N counter, modal viewer |
| Heatmap · $/ha | ✓ | Green-to-red gradient + legend |
| Heatmap · lot area | ✓ | Blue-to-yellow gradient + legend |
| Photon geocoder | ✓ | Real address search (Calle Palma, Asunción, etc.) |
| Keyboard navigation in search | ✓ | ArrowDown/Up, Enter, Escape |
| Anchor city radius circles (30km) | ✓ | 20 cities, intensity = listing density |
| Mobile drawer (sidebar) | ✓ | Hidden by default, hamburger menu |
| Mobile filter sheet | ✓ | Bottom sheet with 6 filters |
| Mobile touch targets ≥44px | ✓ | Apple HIG-compliant |
| WCAG 2.2 AA | partial | Skip-link, focus-visible, prefers-contrast, prefers-reduced-motion |
| A11y: prefers-reduced-motion | ✓ | CSS media query |
| A11y: prefers-contrast (more) | ✓ | CSS media query |
| Light mode toggle | ✓ | Dark / auto / light, persisted in localStorage |
| Print stylesheet | ✓ | Clean B&W map printout, grayscale tiles |
| PII scrubbed | ✓ | 10,898 listings, agent phones/emails → null |
| Market signals (auto) | ✓ | Live compute: 10,898 listings, median $90K, refresh ↻ |
| NASA POWER 12-month strip | ✓ | Color-coded temp + precip by month |
| INBIO choropleth P95 scale | ✓ | Stable scaling, non-producing deptos dim |
| Share view button | ✓ | URL with lat/lon/z/layers |
| Embed widget (?embed=1) | ✓ | Hides sidebar |
| Geolocation | ✓ | One-click find me |
| URL hash sync | ✓ | ?lat=&lon=&z=&layers= |
| CSV export (filtered) | ✓ | 16 columns, current snapshot |
| Filter by price/type/beds/area | ✓ | Live filter, re-cluster + rebuild heatmap on apply |
| Fair-price ML | ⚠️ | R² ≈ 0.017; UI decoration only |
| Yield calculator | ✓ | Gross/net yield, payback years |
| Lang switcher (es/en/gn) | partial | EN/ES work, GN falls back to ES |
| PWA installable | ✓ | Manifest, service worker, beforeinstallprompt |
| Toast notifications | ✓ | Success / error / info types |
| PWA install + offline | ✓ | Service worker registered, install prompt |
| Theme toggle (dark/auto/light) | ✓ | Persisted in localStorage |
| Cloudflare Web Analytics | ready | Token placeholder; activate once CF issues token |

## National hillshade (2026-07-13)

- ✓ Four bbox-cropped Copernicus GLO-30 regional JPEGs generated (`nw`, `ne`, `sw`, `se`), each 6000×6000 px.
- ✓ Chunked Horn computation preserves all raster columns and is covered by regression tests.
- ✓ National overlay loader registers all four quadrants; priority-city terrain still loads on demand at zoom ≥11.
- ✓ Build can resume selected quadrants with `python3 scripts/build_paraguay_hillshade_v3.py --regions <names>` and exits non-zero if any region fails.

## Known issues / what's NOT done

- **No auto-refresh** — data is whatever the last scrape produced. Will go stale.
- **No user accounts / cloud sync** — saved listings are localStorage only.
- **GN (Guaraní)** — falls back to ES (no GN translations yet).
- **10,898 properties' geo accuracy** — relies on source data; ~339 have unknown depto.
- **5,649 properties with PII scrubbing** — agent phones null, no leak check on emails beyond @-pattern.
- **Limited automated coverage** — hillshade builder/frontend regressions are automated; most remaining functionality still relies on ad-hoc shell/Playwright scripts.
- **No CI** — manual `wrangler deploy`.
- **No monitoring** — no uptime check, no error reporting.

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

## Live deploy probes (verified 2026-08-14)

The custom domain `geodata.paragu-ai.com` (and alias `datos.paragu-ai.com`) was
returning **HTTP 404** from 2026-08-10 until 2026-08-14 because the catch-all
CF Worker `aiw-fallback` (route `*.paragu-ai.com/*`) was returning 404 for these
hosts before traffic reached the CF Pages project.

**Fix:** Updated `aiw-fallback` (in CF account `9eb1832f3e42a1dbd6ba854f8d6a1cb2`)
to forward `geodata.paragu-ai.com` and `datos.paragu-ai.com` to the
`paraguay-geodata` CF Pages origin (`paraguay-geodata.pages.dev`). Canonical
source now lives in `Ai-Whisperers/infrastructure/workers/aiw-fallback.js` with
a deploy workflow in `.github/workflows/deploy-worker.yml`.

**Deploy pipeline:** `.github/workflows/deploy.yml` (CF Pages via
`cloudflare/pages-action@v1`) auto-deploys `exports/web/` on every push to
`main` touching `exports/web/**`. Worker deploy pipeline in
`Ai-Whisperers/infrastructure`.

**Probe results (2026-08-14):**

| URL                                              | Status | Size       |
|--------------------------------------------------|--------|------------|
| `https://paraguay-geodata.pages.dev/`            | 200    | 81,354 B   |
| `https://geodata.paragu-ai.com/`                 | 200    | 81,713 B   |
| `https://geodata.paragu-ai.com/mapa.html`        | 200    | 16,810 B   |
| `https://geodata.paragu-ai.com/datos.html`       | 200    | 39,718 B   |
| `https://geodata.paragu-ai.com/manifest.webmanifest` | 200 | 1,166 B   |
| `https://geodata.paragu-ai.com/data/properties_latest.geojson` | 200 | 19,007,147 B |
| `https://geodata.paragu-ai.com/data/tile_index.json`         | 200 | 3,770,820 B |
| `https://geodata.paragu-ai.com/data/roads.geojson`           | 200 | 5,809,132 B |
| `https://geodata.paragu-ai.com/data/buildings_asuncion.geojson` | 200 | 13,552,078 B |
| `https://geodata.paragu-ai.com/data/water.geojson`           | 200 | 2,584,577 B |
| `https://geodata.paragu-ai.com/data/admin/catastro_dpto.geojson` | 200 | 35,521 B |
| `https://geodata.paragu-ai.com/data/ml/fair_price_model.json` | 200 | 5,962 B   |
| `https://datos.paragu-ai.com/`                   | 200    | 81,713 B   |
| `https://datos.paragu-ai.com/mapa.html`          | 200    | 16,810 B   |

**To re-verify any time:**

```bash
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
for url in \
  "https://paraguay-geodata.pages.dev/" \
  "https://geodata.paragu-ai.com/" \
  "https://geodata.paragu-ai.com/mapa.html" \
  "https://geodata.paragu-ai.com/data/properties_latest.geojson" \
  "https://datos.paragu-ai.com/mapa.html" ; do
  curl -s -o /dev/null -w "%{http_code} %{size_download}B  $url\n" --max-time 10 -A "$UA" "$url"
done
```
