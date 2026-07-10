# Properties Pipeline — Operations Playbook

The Phase 2 + 3 deliveries that turn `paraguay-geodata` from "satellite tiles" into "properties for sale + price overlay".

## What we're scraping

Three PY real-estate portals (priority order based on inventory density):

1. **infocasas.com.py** — largest, most listings, has phone + landlord + price bands
2. **propiedades.com.py** — second-largest, more investment-grade listings (often through realtors)
3. **baiker.com** — focused on lands (fincas, estancias) + rural properties

We **do not** target MercadoLibre's real-estate vertical — it's an aggregator with 1-2 day cache; we get better data direct from the portals.

## What we're cross-referencing against

Operator-supplied `data/cadastre/escrituras/*.csv` — these are the **anchors**. Every time a property is bought/sold via a real notary (Escribanía), we get:
- Exact transaction price (USD or PYG-converted)
- Exact area (hectares or square metres)
- Exact centroid (lat/lon) of the lot
- District + Departamento

We don't ship the deeds publicly (PII risk on owners). We **DO** ship the (lat, lon, $/ha) tuples as cross-reference anchors for the kriging model.

## Why scrape if API exists?

Because it doesn't (yet). Paid services like Properati charge $200/mo for Paraguay coverage; we have the time, the bandwidth, and the ethics gate.

See `docs/ethics/scraper-policy.md` for the guardrails.

## Listings + escrítura schema

Draft (Phase 2 will formalise as `docs/specs/listing-schema.json`):

```json
{
  "type": "Feature",
  "geometry": { "type": "Point", "coordinates": [-57.5759, -25.2637] },
  "properties": {
    "id": "ic_<hash>",                  // sha1(source + source_id)
    "source": "infocasas",
    "source_id": "v12345",
    "source_url": "https://infocasas.com.py/anuncio/v12345",
    "scraped_at_utc": "2026-07-10T22:00:00Z",
    "price_usd": 95000,                 // converted at scrape-time FX
    "price_pyg": 715000000,
    "area_ha": 0.5,
    "$/ha": 190000,                     // derived = price_usd / area_ha
    "district": "Sajonia",
    "departamento": "Central",
    "attrs": {
      "bedrooms": 3,
      "bathrooms": 2,
      "has_water": true,
      "has_power": true,
      "has_road_access": true,
      "land_use": "residential"
    },
    "escritura_anchor_id": null,        // populated by cross-ref
    "escritura_distance_m": null,
    "price_band_vs_anchors": null       // populated by cross-ref: "in_band", "above_2x", "below_half"
  }
}
```

## Scraping arch

| Job | Cron | Frequency | Output |
|---|---|---|---|
| `paraguay-geodata-fetch-properties` | Sun 03:00 PY | weekly | `data/properties/snapshots/<date>.geojson` + diff vs prior snapshot |
| `paraguay-geodata-build-price-surface` | Sun 05:00 PY | weekly | `data/prices/departamento_<id>_$/ha.tif` |
| `paraguay-geodata-rebuild-properties-deploy` | Sun 06:00 PY | weekly | `exports/web/data/properties_<date>.geojson` + `export/web/data/price_surface_<date>.geojson` (≤25 MiB) + CF Pages redeploy |

(All cron entries registered in `~/.hermes/cron/jobs.json` post-Phase 1.)

## Deduplication

Three layers of dedup:

1. **By `(source, source_id)`** — primary key per portal. Listings have stable IDs in their URLs (`/anuncio/<id>`).
2. **By geospatial hash** — same property listed on 2 portals within 50m + same price band + same area → merge into one record (`source_count: 2`, `source_ids: [...]`).
3. **By escritura anchor** — when a deed is filed, cross-check the latest listings snapshot for any record within 200m + similar area + similar price, mark as `escritura_anchor_id: <deed_id>`. Future scrapes can use this to detect re-listing or stale prices.

## Rate-limit + politeness

Per `docs/ethics/scraper-policy.md` (gating document):
- 50 HTTP req/min/portal (~2.4M req/mo — well under any commercial-portal ToS threshold)
- Respect `robots.txt` — default-respect or stricter
- User-Agent: `paraguay-geodata/0.1 (+https://github.com/Ai-Whisperers/paraguay-geodata; contact: iván@ai-whisperers.org)`
- Backoff on HTTP 429/503 (exponential, max 60s)
- Cache every page for 6 hours before re-requesting same URL

## Phase 2 sequencing (one commit per step)

1. `tools/fetch_properties.py` — read-only scraper, no DB, dumps raw JSON to stdout
2. Add Onto the listing-schema.json + `data/properties/`
3. Build dedup logic (`scripts/dedupe_listings.py`)
4. Cross-reference against escritura anchors (`scripts/match_escrituras.py`)
5. `tools/build_price_surface.py` — kriging + per-departamento output
6. `exports/web/properties.html` — listings + price-heatmap overlay
7. `exports/web/properties/snapshot_<date>.geojson` — public snapshot endpoint
8. Cron registration + first weekly run

## Open questions (Phase 2 will answer)

- How many escritura anchors do we need to get kriging below the RMSE ceiling?
  - Hypothesis: ~5-10 anchors per departamento for rural + ~20-50 for urban Central/Asunción area.
- What's the right kriging variogram for each departamento? (Likely exponential with range ~5-50 km.)
- Is the infocasas landlord cell phone in the public scraping? **Yes** (their listing page shows it). We should strip it from the public snapshot (PII). Keep in raw private snapshot for analysis only.
