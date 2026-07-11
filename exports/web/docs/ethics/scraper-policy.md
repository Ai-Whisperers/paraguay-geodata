# Scraper Policy — Ethical Gate

Run before `tools/fetch_properties.py` ships, and again before any new portal scraper is added. This is the protocol decision tree — explicit enough that a non-technical operator can audit, fast enough that an AI agent doesn't bypass it.

## Decision tree

```
                     Is the content inside a login?
                            \
                            \
                          (yes) ─────────────────────────── STOP. Do not scrape.
                            │                               Alternative: surface the URL
                            │                               in /properties.html and let
                            │                               user click-through.
                          (no)
                            │
                     Does robots.txt forbid this user-agent?
                            │
                            │
                          (yes) ─────────────────────────── STOP. Always respect robots.txt.
                            │                               If you own operator rights or have
                            │                               explicit written permission, document it.
                          (no)
                            │
                     Are the listings public (no auth required)?
                            │
                            │
                          (yes) ─────────────────────────── PROCEED.
                            │                               At the limits defined below:
                            │                               - Rate limit ≤ 50 req/min/portal
                            │                               - Cache every URL 6 hours
                            │                               - Strip PII from public snapshot
                            │                               - Respect HTTP 429 / 503 with backoff
                          (no) ─────────────────────────── STOP. See above.
```

## Why this exists

The operator has a business reputation to protect and a legal responsibility to the portals being scraped. The default-action in any ambiguity is **stop and ask** — never "ship and apologise later".

## What's public for each target portal (Phase 2 candidates)

| Portal | Public listings? | robots.txt blocks scraping of `/anuncio/*`? | Login required for detail? | Decision |
|---|---|---|---|---|
| infocasas.com.py | Yes | No (or only opaque `Disallow: /admin`) | No | **Scrape** at 30 req/min |
| propiedades.com.py | Yes | No | No | **Scrape** at 30 req/min |
| baiker.com | Yes | No | No | **Scrape** at 30 req/min |
| mercadolibre.com.py | Yes (real-estate vertical) | Yes — `Disallow: /jm/*` | No | **Do not scrape** listings-detail; rely on MercadoLibre's RSS or paid API if available |
| encuentrobienes.com | Yes | No | No | **TBD** — defer to Phase 2.1 |
| adinco.com.py | Aggregator, not source | (irrelevant) | (irrelevant) | Do not scrape; cite as upstream feed if relevant |

(Each verdict ratified by `tools/fetch_properties.py --portal <name> --dry-run` which probes robots.txt + 2 random listing URLs before adding it to the active scraper list.)

## Rate & politeness limits (all scrapers, all portals)

```yaml
max_req_per_minute_per_portal:  50         # 2.4M req/mo — well below commercial thresholds
max_concurrent_requests:        3          # strict, no bandwidth surge
default_page_cache_hours:       6          # don't re-request same URL during business day
backoff_on_429_sec:             [30, 60, 120]  # exponential, max 2 minutes
backoff_on_503_sec:             [60, 120, 240]
user_agent_string:              "paraguay-geodata/0.1 (+https://github.com/Ai-Whisperers/paraguay-geodata; contact: iván@ai-whisperers.org)"
sleep_between_pages_sec:        1.0        # minimum
sleep_between_portals_sec:      5.0        # when scraping multiple portals back-to-back
retry_on_timeout:               max 2 attempts, then skip URL
max_listings_per_run:           5000       # sanity ceiling per weekly run
output_dir_size_cap_mb:         500        # raw snapshot, before dedup + PII-strip
```

These are **defaults in `tools/fetch_properties.py`** — overrides require a code comment with the operator's explicit written rationale.

## PII strip rules (operational)

Field-by-field rules for what gets stripped from the public snapshot vs the raw snapshot:

| Field | Public snapshot? | Raw snapshot (private)? | Why |
|---|---|---|---|
| `id` (hash) | ✅ | ✅ | not PII |
| `source` + `source_id` | ✅ | ✅ | not PII |
| `source_url` | ✅ | ✅ | not PII; user wants to click through |
| `lat/lon` (rounded to 100m) | ✅ | ✅ exact | exact lat/lon of a private property is borderline-privacy (reveals street/doorway for some urban listings); 100m rounding is the conventional compromise |
| `price_usd` + `price_pyg` | ✅ | ✅ | not PII in Paraguay context |
| `area_ha` | ✅ | ✅ | not PII |
| `$/ha` | ✅ | ✅ | derived, not PII |
| `attrs.bedrooms`, `bathrooms` | ✅ | ✅ | not PII |
| `attrs.has_water/power/road` | ✅ | ✅ | not PII |
| Landlord email | ❌ NEVER | ⚠️ optional | PII; raw snapshot only if operator asks |
| Landlord phone (raw string) | ❌ strip last 4 digits | ⚠️ optional | PII; redact for public |
| Landlord name | ❌ | ✅ if visible | PII; strip from public |
| Photos URLs that link to landlord's social media | ❌ | ⚠️ optional | cross-link fingerprinting risk |
| Any field showing real estate agency marketing copy | ❌ | ✅ | free text = re-publication liability; we don't get it anyway |

For `data/properties/raw/<snapshot>.geojson` (private — gitignored): keep all fields for analysis. For `exports/web/data/properties_<date>.geojson` (public): apply the strip table above.

## What we don't scrape (even if "public")

1. **Anything behind a login.** No ifs/ands/buts. If a portal sets a cookie and gives you a personalised feed, we don't take it from them.
2. **Anything that costs the operator money.** Some portal listings are "premium" with their owners; they pay to be on top. Scraping those *de-facto* suppresses their value proposition. We scrape all listings as listed by the HTML sitemap/listing index.
3. **Anything that re-publishes someone else's copyrighted photos at high res** without attribution. We use a thumbnail at <800 px max.
4. **Anything the portal is clearly blocking** (after respecting robots.txt and rate limits). If we get 24 hours of 100% 429s, that's the portal telling us. Stop.

## When to revisit the gate

- Every quarter: re-check robots.txt of each portal (they can change without notice).
- When a portal changes its URL structure (e.g. infocasas switches from `/anuncio/<id>` to `/properties/<id>`): the scraper must NOT auto-follow links; page operator first.
- When the operator adds a new portal: ethics gate re-runs from the top.

## Operator-facing audit checklist (quarterly)

```bash
# 1. Confirm robots.txt still permits scraping
for p in infocasas.com.py propiedades.com.py baiker.com; do
  curl -sS "https://$p/robots.txt" | head -30 | sed "s/^/[$p] /"
  echo
done

# 2. Confirm raw snapshot cap is respected
du -sh data/properties/raw/  # should be < 500 MB

# 3. Confirm no PII leaked to public snapshot
python3 -c "
import json, sys
with open('exports/web/data/properties_latest.geojson') as f:
    d = json.load(f)
banned = ['landlord_phone', 'landlord_email', 'landlord_name']
hits = 0
for feat in d.get('features', []):
    for b in banned:
        if b in feat['properties']:
            hits += 1
            print(f'LEAK: {b} in {feat[\"properties\"][\"id\"]}')
sys.exit(1 if hits else 0)
"

# 4. Confirm no landlord-targeted scraping happened
grep -E 'phone=|whatsapp=|email=' data/properties/raw/*.geojson 2>/dev/null | head
# (any matches are still allowed in raw; verify they're NOT in exports/web/data/)

# 5. Confirm rate limits haven't been silently overridden
grep -E 'REQUESTS_PER_MINUTE|MAX_CONCURRENT' tools/fetch_properties.py | head
```

## When in doubt

Page the operator. Don't ship. The worst outcome of "we paused and asked" is 30 minutes of conversation; the worst outcome of "we shipped and upset a portal" is a cease-and-desist letter and a public-relations headache.
