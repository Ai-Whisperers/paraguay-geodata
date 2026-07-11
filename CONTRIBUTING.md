# Contributing

## How to contribute

We welcome contributions via GitHub PRs. This is an open civic-data project — anyone can help.

## Quick start

```bash
git clone https://github.com/Ai-Whisperers/paraguay-geodata
cd paraguay-geodata
git checkout -b feature/your-feature

# Make changes to:
# - exports/web/index.html (main viewer)
# - exports/web/data/*.geojson (data layers)
# - exports/web/mapa.html (per-tile viewer)
# - tools/*.py (data pipeline scripts)

# Add a data source
python3 tools/fetch_catastro_parcels.py --sample 1000
# Edit the registry in index.html (LAYER_GROUPS_ORDER + a new entry)
# Add a loader function

# Test
python3 tools/test_endpoints.py
node tools/test_browser.js  # requires playwright

# Commit + PR
git add .
git commit -m "Add: <feature>"
git push origin feature/your-feature
gh pr create --title "Add: <feature>" --body "..."
```

## Code of conduct

- Be respectful
- Data accuracy matters — cite sources
- PII is forbidden — agents' phone/email/name must be scrubbed
- Don't add tracking, ads, or any third-party services without discussion
- Spanish + Guaraní for user-facing strings; English OK for code

## Adding a new data layer

1. **Get the data** (GeoJSON, ideally already in EPSG:4326)
2. **Drop it** in `exports/web/data/<group>/<name>.geojson`
3. **Register it** in `exports/web/index.html`:
   ```js
   layerState.my_layer = { group: 'admin', label: 'My Layer', active: false, features: '?',
                            source: 'Origin', info: 'What this is', color: '#hex',
                            url: 'data/my_layer.geojson' };
   ```
4. **Add to** `LAYER_GROUPS_ORDER` array
5. **Add a loader function**:
   ```js
   async function loadMyLayer() {
       const r = await fetch('./data/my_layer.geojson');
       // ... rest follows same pattern as loadCatastroDpto
   }
   ```
6. **Call it** in the bootstrap section
7. **Test** with `tools/test_endpoints.py`

## Adding a new language

1. Edit `I18N = { ... }` in `exports/web/index.html`
2. Add a new language code: `I18N.pt = { ... }` for Portuguese
3. Add to `<select>` in `addLangSwitcher()` function
4. Add to `applyI18n()` labelMap if it's a stat label

## Adding a new i18n key

1. Add to all 3 languages in `I18N` dict
2. Add `data-i18n="your_key"` to the HTML element
3. (Optional) Add to `labelMap` in `applyI18n()` if it's a stat label

## Adding documentation

- `/docs/research/` — research on data sources
- `/docs/ethics/` — scraping ethics, license analysis
- `/docs/sources/` — specific source documentation
- `/docs/api/` — OpenAPI spec

## Filing issues

Use GitHub Issues for:
- Bug reports (include browser + screenshot)
- Data source suggestions (must be open data)
- Feature requests (be specific about use case)
- Translation corrections (Guaraní especially welcome)

## PII policy

**Strictly forbidden** in public data:
- Agent phone numbers (full or partial)
- Agent email addresses (domain only OK)
- Landlord/owner names
- Tenant names
- Interior photos that show people

**Acceptable:**
- Aggregated counts (e.g., "7330 listings in Asunción")
- Area names, city names, depto names
- Price, area, bedrooms, bathrooms
- Photo URLs from source sites (they're CDN-served)

## License

By contributing, you agree to license your contributions under:
- **Code**: MIT
- **Data additions**: ODbL (Open Database License)
- **Documentation**: CC-BY 4.0