# API Cookbook — Paraguay Geodata

The site exposes a small public REST API at `/api/v1/` plus a series of static
artifacts under `/data/`. This cookbook shows the most useful curls, what
each endpoint returns, and how to compose them into a workflow.

All endpoints are GET, return JSON, and are CORS-enabled. No auth required
for the public endpoints. Rate limits: 60 req/min per IP (Cloudflare default).

## Public endpoints

### `GET /api/v1/facets.json`
The bucket counts that drive the filter UI on the homepage. Useful for
seeing "how many listings match each value" without downloading the full
10,780-listing geojson.

```bash
curl -s https://geodata.paragu-ai.com/api/v1/facets.json | jq '.facets.property_type'
```

```json
[
  { "value": "house", "count": 3751 },
  { "value": "apartment", "count": 3103 },
  { "value": "land", "count": 2604 },
  { "value": "commercial", "count": 717 },
  { "value": "office", "count": 597 },
  { "value": "?", "count": 8 }
]
```

Other facets: `depto`, `currency`, `source`, `features`.

### `GET /api/v1/properties.json`
A tiny index of the dataset — gives the feature count, freshness window,
and date the artifact was generated. Use it as a healthcheck.

```bash
curl -s https://geodata.paragu-ai.com/api/v1/properties.json | jq
```

### `GET /api/v1/geojson?...`
Filtered GeoJSON. Pass bbox, property_type, depto, etc. as query params.

```bash
curl -s 'https://geodata.paragu-ai.com/api/v1/geojson?bbox=-57.6,-25.3,-57.5,-25.2&property_type=apartment' \
  | jq '.features | length'
```

Parameters (all optional):
- `bbox=minLon,minLat,maxLon,maxLat` — viewport filter
- `property_type=apartment|house|land|commercial|office`
- `depto=Asunción|Central|Alto Paraná|...`
- `currency=USD|PYG`
- `source=infocasas|tulugar|asuncion_estate|inmueblespy`
- `min_price=0`, `max_price=999999999`
- `min_area=0`, `max_area=999` (hectares)
- `bedrooms=0` for `0+`, `3` for `3+`

### `GET /data/properties_latest.geojson`
The full canonical artifact (~18 MB). Download once and filter locally.

```bash
curl -o /tmp/paraguay.geojson https://geodata.paragu-ai.com/data/properties_latest.geojson
jq '.features | length' /tmp/paraguay.geojson
# 10780
```

### `GET /data/properties_enriched_lite.geojson`
A 3.9 MB subset with only essential fields (id, price, area, type, coords).
For mobile-first widgets that don't need full descriptions.

```bash
curl -s 'https://geodata.paragu-ai.com/data/properties_enriched_lite.geojson' \
  | jq '.features[0].properties'
```

```json
{
  "id": "tulugar-12345",
  "title": "Departamento en Recoleta",
  "price_usd": 95000,
  "area_ha": 0.0080,
  "property_type": "apartment",
  "state_province": "Asunción",
  "currency": "USD"
}
```

### `GET /data/data_freshness.json`
How fresh is the data? This is the canonical "deploy metadata" for the
listings artifact.

```bash
curl -s https://geodata.paragu-ai.com/data/data_freshness.json | jq
```

```json
{
  "as_of_utc": "2026-08-04T...",
  "feature_count": 10780,
  "median_days": 1,
  "min_date": "2026-07-11T...",
  "max_date": "2026-08-04T..."
}
```

### `GET /data/deploy-meta.json`
When was the site last deployed, by whom, at what commit?

```bash
curl -s https://geodata.paragu-ai.com/data/deploy-meta.json | jq '{commit, deployer, deployed_at_utc}'
```

### `GET /data/duplicate_clusters.json`
Cross-source duplicates — 50 clusters covering 101 listings. Useful for
"show me a listing that's also on Infocasas" badges.

```bash
curl -s https://geodata.paragu-ai.com/data/duplicate_clusters.json | jq '.clusters | length'
# 50
```

### `GET /data/bcp_rates.json`
USD/PYG reference rate (BCP API or stub). The 30-day rolling average is
used to flag listings as "USD stable" in the popup.

```bash
curl -s https://geodata.paragu-ai.com/data/bcp_rates.json | jq
```

```json
{
  "as_of_utc": "2026-08-04T...",
  "pyg_per_usd": 7500,
  "pyg_per_usd_30d_avg": 7500,
  "source": "stub"
}
```

### `GET /data/properties.pmtiles`
Vector tiles for the map (520 KB). The map loads these client-side.

### `GET /healthz.json`
Site health probe. Returns `{"status":"ok"}` if reachable.

```bash
curl -s https://geodata.paragu-ai.com/healthz.json | jq
```

### `GET /bulletin.json`
What's new (changelog + roadmap). Used by the on-page bulletin widget.

### `GET /sitemap.xml`
23 URLs covering the main pages + API endpoints + data artifacts.

### `GET /status.html`
Human-readable status page with link health.

## Static downloads

### GeoJSON of an architect bundle
Asunción only (~700 KB):
```bash
curl -O https://geodata.paragu-ai.com/data/architect_export_asuncion.geojson
```

Full national (~3.3 MB):
```bash
curl -O https://geodata.paragu-ai.com/data/architect_export.geojson
```

These include construction zones + urban zoning + flood + climate + hillshade
layers in one file. Open in QGIS / ArcGIS / AutoCAD Map 3D.

## Workflows

### "I want to build a price-per-depto heat map"
```bash
# 1. Get the geojson
curl -O https://geodata.paragu-ai.com/data/properties_latest.geojson

# 2. Filter to Asunción apartment listings
jq -c '.features[] | select(.properties.state_province == "Asunción" and .properties.property_type == "apartment")' paraguay.geojson > asu-apt.jsonl

# 3. Compute price per sqm, group by barrio
jq -r '[.properties.barrio, .properties.price_usd / (.properties.area_ha * 10000)] | @tsv' asu-apt.jsonl | \
  awk '{sum[$1]+=$2; n[$1]++} END {for (k in sum) printf "%s\t%.0f\n", k, sum[k]/n[k]}' | \
  sort -k2 -n -r
```

### "Show me new listings from the last 7 days"
```bash
curl -s https://geodata.paragu-ai.com/api/v1/geojson | \
  jq -r '.features[] | select(.properties.last_seen_at > (now - 604800 | todate)) | .properties.title'
```

### "Get a CSV of all listings in my viewport"
The frontend has a "CSV (filtrado)" button under the architect export panel
that calls `window.exportCSV("filtered")`. This produces a UTF-8 BOM-prefixed
CSV with 18 columns. The same goes for XLSX.

## Rate limits

Cloudflare's free tier provides 100,000 requests/day per IP. The static
artifacts (`/data/*.geojson`, `/data/*.json`) are cached at the edge for
5-10 minutes.

If you need higher rate limits or a different endpoint, open an issue at
https://github.com/Ai-Whisperers/paraguay-geodata/issues.

## Schema discovery

The site publishes Schema.org Dataset markup in its `<head>`. Google and
other crawlers can read the dataset metadata:

```bash
curl -s https://geodata.paragu-ai.com/ | \
  grep -oP '<script type="application/ld\+json">\K.*?(?=</script>)' | \
  jq '. | {name, description, license, spatialCoverage, temporalCoverage}'
```