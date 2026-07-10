# PROVENANCE

Source data lineage, license summary, and per-file chain of custody.

## Source stack

```
Upstream data providers (free / open)
  │
  ├── Copernicus GLO-30              (ESA, free)
  ├── Sentinel-2 L2A                (ESA + Microsoft Planetary Computer, free)
  ├── Esri World Imagery            (Esri, free for tiles ≤ z=19)
  ├── OSM                           (OpenStreetMap contributors, ODbL)
  ├── MapBiomas Paraguay            (CC BY 4.0)
  ├── Hansen GFC                    (CC BY 4.0)
  ├── JRC Global Surface Water      (EC, free)
  ├── HydroSHEDS                    (CC BY 4.0)
  ├── NASA FIRMS                    (public domain)
  ├── GBIF                          (per-record: CC0 / CC BY / CC BY-NC)
  ├── SoilGrids                     (CC BY 4.0)
  │
  ├── listings (infocasas, propiedades, baiker)    (see ethics/scraper-policy.md)
  └── escrituras (operator-supplied anchors)
       │
       ▼
Tools (Py / bash / Node)
  │
  ├── tools/national_tile_index.py          ── input bbox → tile_index.json
  ├── tools/fetch_tile.py                   ── per-tile orchestrator
  ├── tools/fetch_<source>.py               ── per-source fetcher
  ├── tools/build_<derived>.py              ── derived layers (cerros, streams, ...)
  └── tools/build_price_surface.py          ── Phase 2: kriging
       │
       ▼
Outputs
  │
  ├── data/tiles/<id>/                  (gitignored raw + derived)
  ├── exports/web/data/tiles/<id>/      (CF Pages: small GeoJSONs + thumbnails)
  └── exports/big_data_excluded_from_deploy/   (R2: heavy rasters)
       │
       ▼
  CF Pages deploy → paraguay-geodata.pages.dev (provisional)
```

## License matrix

| Output | License | Backed by |
|---|---|---|
| Code (`.py`, `.sh`, `.js`) | MIT | this repo's `LICENSE` |
| `exports/web/data/**/*.geojson` (we publish as our work) | CC0 1.0 | derived from upstream sources |
| `exports/web/data/**/*.png` (rendered by our tools) | CC0 1.0 | derivations |
| Tiles we compose from MapBiomas / Hansen / OSM | depends on source | original license preserved |
| Listings snapshots (raw) | private (gitignored) | per-portal ToS |
| Listings snapshots (public) | CC0 1.0 after PII strip | our work + scraped public URLs (cite source per record) |

## Operating principles

1. **Per-record attribution** lives in `metadata.attribution` whenever we ship derived data. Example:
   ```json
   { "metadata": { "attribution": "MapBiomas Paraguay (CC BY 4.0) — https://plataforma.mapbiomas.org", "source_date": "2023-12-31" } }
   ```
2. **License downgrades** are explicit. If we can't comply with a source's share-alike, we don't ship that source — only the upstream URL.
3. **PII**: listings with PII never make it to `exports/web/data/`. Always to `data/properties/raw/` only (gitignored, internal).
4. **Portal scrapers**: ethics gate ratified in `docs/ethics/scraper-policy.md` before any scrape.

## What this file IS NOT

- Not a `PROVENANCE.md` for the website itself (no website yet).
- Not the unit test for correctness — that's `tests/`.
- Not a license file — see `LICENSE` (MIT only covers code).

## Update cadence

Every time a new upstream source is integrated (Phase 1/2), update:
- This file's `Source stack` + `License matrix` tables
- `CREDITS.md` row for the provider
- The relevant `docs/sources/<source>.md` file (newly created or extended)
