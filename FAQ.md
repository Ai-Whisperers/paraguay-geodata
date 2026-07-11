# FAQ

## General

### What is this?
An open civic-data platform for Paraguay. Live national map of real-estate, cadastral, environmental, and infrastructure data. Free, no auth, no tracking.

### Why Paraguay?
Under-served by open data tooling. Catastro Nacional is online but not widely used. Most real-estate data is fragmented across portals. This platform unifies them.

### Is this free?
Yes. Code: MIT. Data: ODbL + various open licenses (see below).

### Can I use this commercially?
For the data: yes, per the source licenses (mostly ODbL). For the code: yes (MIT).

### Who built this?
Open contribution via GitHub. Initial deployment by Ai-Whisperers.

## Data

### How fresh is the data?
Last refresh: tracked in `/data/data_freshness.json` + shown as "Xh ago" badge in sidebar. Currently refreshed manually.

### Where does the data come from?
- **Properties:** Infocasas (UY aggregator, has PY listings) + TuLugar (PY portal) + Clasipar (PY portal)
- **Cadastre:** Catastro Nacional WFS (official Paraguay land registry)
- **OSM:** Geofabrik Paraguay extract (315 MB)
- **Agriculture:** INBIO (Instituto de Biotecnología Agrícola)
- **Biodiversity:** GBIF
- **Macro:** BCP (Banco Central del Paraguay)
- **Climate:** NASA POWER

### Why only 10,898 properties?
That's what we could scrape ethically. More sources (Clasipar detail pages, RE/MAX via Playwright, Propietarios Directos) are queued in `/docs/research/PROPERTY_HOUSING_DATA_SOURCES.md`.

### Can I add my own data source?
Yes. See `CONTRIBUTING.md` → "Adding a new data layer". Open data preferred.

### Is the geo accuracy good?
Property coords are from the source platforms. ~95% are within ~100m of true position; ~5% are depto-level only. We do not verify; we display what sources report.

### Why are 529 listings "Unknown" depto?
Source data didn't include depto. We reverse-geocode via Photon on load (best-effort, 50 at a time to avoid rate limit).

## PII

### Why no agent phone numbers?
LGPD-style privacy. Agent phones are PII. We never publish them. Even if data sources include them, we scrub before publish.

### Why no landlord names?
Same. PII. Not public.

### What about photos from listings?
Yes — photos are hot-linked from source CDNs. They're public marketing material, not personal data.

## Technical

### What technology is this?
- Leaflet (maps) + Chart.js (charts) + Photon (geocoder)
- Static Cloudflare Pages hosting (no server)
- Vanilla JS, no build step
- Service worker for offline

### Why no React/Vue/Next?
Static HTML + CDN libraries loads in <2s with no build complexity. Better for civic-data tools that need longevity (no dependency churn).

### How do I deploy my own?
1. Fork the repo
2. Install wrangler: `npm install -g wrangler`
3. Run: `wrangler pages deploy exports/web --project-name=your-project`
4. (Optional) Add custom domain in Cloudflare dashboard

### Is there an API?
Yes. The 21 GeoJSON endpoints ARE the API. No auth required. Add OpenAPI spec at `docs/api/openapi.yaml`.

### Can I see historical changes?
Not yet — `tools/track_price_history.py` generates a JSON file but it's not deployed. Roadmap item.

### How do I report a bug?
GitHub Issues: https://github.com/Ai-Whisperers/paraguay-geodata/issues

## Privacy / Legal

### Does this track me?
No. No analytics. No cookies. No third-party trackers. Only one service worker for offline caching.

### What about GDPR / LGPD?
Not applicable (this is Paraguay, not EU). But we follow the principles: no PII, no tracking, no cookies.

### Can I request removal of my listing?
Yes. Open an issue with the source_id + source. We'll remove within 7 days.

## Roadmap

### What's next?
- Auto-refresh pipeline (cron-based)
- Vector tiles (MVT) for OSM roads
- User accounts + saved searches (optional)
- Indigenous territory legal-boundary data (if INDI releases)
- Real-time deforestation alerts via Hansen/GLAD

### What's NOT on the roadmap?
- Mobile native app (PWA suffices)
- B2B SaaS pricing (this is open data)
- Stripe Connect (no payments — listings are scraped, not user-submitted)

## Contributing

See `CONTRIBUTING.md`.