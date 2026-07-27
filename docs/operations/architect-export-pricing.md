# Architect Map Download — Paid Offering

**Shipped:** 2026-07-14
**Repo:** `Ai-Whisperers/paraguay-geodata`
**Worker:** `exports/checkout-worker/` (Cloudflare Worker)
**Live:** https://geodata.paragu-ai.com/

## Why this exists

Architects (Lucía-style users), real-estate developers, and surveyors regularly
need to pull **raw vector data** out of the platform — not just view it. The
existing CSV/KML exports cover the spreadsheet/Google-Earth crowd, but two
formats are required to win the architect segment:

- **GeoJSON** — the lingua franca of GIS (QGIS, ArcGIS, Mapbox Studio, every
  web map library)
- **DXF** — AutoCAD's text-based interchange format, readable by every CAD tool
  on the planet (AutoCAD, BricsCAD, IntelliCAD, SketchUp, even QGIS). DWG is
  the same data in a binary container; AutoCAD itself reads DXF natively and
  offers one-click Save-As DWG, so DXF is the right format to ship.

## Product tiers

| Tier | Format | Scope | Price | Use case |
|---|---|---|---|---|
| Free | GeoJSON | viewport (what's on screen) | $0 | Quick export of a city/region you're looking at |
| Free | GeoJSON | filtered (current UI filters) | $0 | Same as CSV/KML today, but as a real GIS file |
| Free | GeoJSON | polygon selection | $0 | User draws a bbox, exports just that |
| Free | DXF | viewport / filtered / selection | $0 | Architect gets CAD-friendly data for the area they're inspecting |
| **Paid** | **GeoJSON** | **full national dataset (~11K listings, PII-scrubbed)** | **$29 one-time** | One-shot national import into their GIS |
| **Paid** | **DXF** | **full national dataset** | **$99 one-time** | One-shot CAD import for whole-country planning |
| Pro | Both | full dataset, refreshed monthly | $299/year | Recurring data refresh for active firms |

The free tiers ship immediately on click — no auth, no friction. The paid
tiers gate behind a Stripe Checkout session hosted at
`https://geodata-checkout.paragu-ai.workers.dev`.

## UX flow

```
[ Map controls ▾ ]
   ⬇ CSV                  ← (free, existing)
   ⬇ KML                  ← (free, existing)
   ⬇ Architect ▾          ← (new — opens dropdown)
       ⬇ GeoJSON · viewport       (free, browser-side blob)
       ⬇ GeoJSON · filtered       (free, browser-side blob)
       ⬇ GeoJSON · all · $29      →  Stripe Checkout
       ⬇ DXF · viewport           (free, browser-side blob)
       ⬇ DXF · filtered           (free, browser-side blob)
       ⬇ DXF · all · $99          →  Stripe Checkout
       View pricing →             (links to /pricing)
```

After successful payment, Stripe redirects to the worker at
`/success?session_id=...&product=...`. The worker:

1. Verifies `payment_status === 'paid'` against Stripe
2. Issues an HMAC-signed download token (1-hour TTL)
3. Redirects to `/download?token=...&product=...` which streams the dataset

## Files

| File | Purpose |
|---|---|
| `exports/web/index.html` | Frontend: GeoJSON + DXF export functions + download menu UI + CSS |
| `exports/web/architect-plan.html` | **Printable plan PDF page** — captures current map view bbox/zoom/center, renders construction zones + urban zoning + flood polygons on Leaflet, includes scale bar, north arrow, legend, layer toggles. Free (no Stripe gate). Architects hit Ctrl+P / Cmd+P → "Guardar como PDF" → A4 landscape → márgenes Mínimos. |
| `exports/checkout-worker/src/worker.js` | Cloudflare Worker: Stripe checkout, success redirect, signed download |
| `exports/checkout-worker/wrangler.toml` | Worker config (route, R2, KV bindings) |
| `exports/checkout-worker/package.json` | Wrangler + Stripe npm |
| `exports/checkout-worker/test/handler.test.mjs` | HMAC sign/verify + catalog unit tests (6 tests, all pass) |
| `exports/checkout-worker/.env.example` | Required env vars + initial test-mode Stripe price IDs |
| `scripts/build_architect_export.py` | Builder for the consolidated GeoJSON bundles (national + Asunción) |
| `tests/test_architect_export.py` | Smoke tests for the builder (4 tests, all pass) |

### Printable plan PDF vs paid export — why both?

- **Free printable plan PDF** (`architect-plan.html`): for the architect who needs
  a *visual artifact* for a client meeting or planning office — same data, paper-ready,
  A4 landscape, scale bar + north arrow + legend. No Stripe, no checkout, opens in
  any browser.
- **Paid raw exports** (GeoJSON/DXF, $29–$99): for the architect who needs to
  *import the data into QGIS/AutoCAD* and work with it offline in their CAD tool of
  choice. That's a different value (data ownership, machine-readable, reprojectable).

They complement each other — the printable PDF is the "show the client what we
see" artifact; the paid export is the "give me the data so I can build from it" artifact.

## Stripe test-mode artifacts (already created)

| Resource | ID | Notes |
|---|---|---|
| GeoJSON one-time price | `price_1TxwVCKHq6GxbJ56JeS6bliT` | $29 USD |
| DXF one-time price | `price_1TxwVUKHq6GxbJ56CF3h2bcP` | $99 USD |
| Pro yearly subscription price | `price_1TxwVUKHq6GxbJ56KxMar2Yc` | $299 USD/yr |

For live deployment:
1. Switch to Stripe live mode in the dashboard
2. Create matching prices (or reuse the test prices after activation — Stripe
   recommends creating fresh live-mode prices, not porting IDs)
3. `wrangler secret put STRIPE_SECRET_KEY` with the live key
4. `wrangler secret put DOWNLOAD_TOKEN_SIGNING_KEY` with a fresh 32-byte hex

## Deploy steps

```bash
cd exports/checkout-worker

# 1. Install deps (wrangler + stripe)
npm install

# 2. Run unit tests
node test/handler.test.mjs     # 6 tests, expect ALL TESTS PASS

# 3. Set secrets
wrangler secret put STRIPE_SECRET_KEY
wrangler secret put DOWNLOAD_TOKEN_SIGNING_KEY
# Optional: publish the dataset to R2 or a Pages deploy, then
#   wrangler secret put DATASET_BASE_URL

# 4. Create R2 bucket for the artifacts
wrangler r2 bucket create geodata-exports
# Upload the full national artifacts:
wrangler r2 object put geodata-exports/properties_latest.geojson \
  --file ../web/data/properties_latest.geojson
wrangler r2 object put geodata-exports/properties_latest.dxf \
  --file ../web/data/properties_latest.dxf

# 5. Deploy
wrangler deploy

# 6. Configure custom domain (optional)
# In Cloudflare dashboard → Workers → geodata-checkout → Triggers
#   add route: geodata-checkout.paragu-ai.workers.dev/*
```

## Roadmap (post-launch)

- [ ] **Per-project pricing** (à la cartographer / architect case study):
  user defines a bbox in the UI → we quote a one-time price based on
  area + dataset intersection → Stripe Checkout.
- [ ] **Volume discounts**: subscription tier that includes 5 / 20 / 100
  one-time dataset exports per month.
- [ ] **Subscription downloads**: monthly refreshed GeoJSON + DXF bundle
  delivered to subscribers via email link or webhook to their own S3.
- [ ] **Webhook to operator dashboard**: every successful payment →
  Slack/Telegram notification with email + product (we already have
  agentcall + telegram wired).
- [ ] **License acceptance**: short click-through on download
  (CC-BY attribution requirement per CREDITS.md).

## Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Architects expect raw DWG, not DXF | High | Med | UI copy says "AutoCAD-readable" + clear note that DXF → DWG is one click in AutoCAD. Consider LibreDWG-powered server-side DWG generator if demand materializes. |
| Dataset is large (~14 MB GeoJSON) | Low | Low | Stripe redirect → direct R2 signed URL — sub-second even on 3G. |
| Token replay / sharing | Low | Med | 1-hour TTL, token bound to Stripe session ID. Log IPs to KV if abuse appears. |
| Chargebacks on disputed purchases | Low | Low | Stripe handles disputes; product is digital and delivered, so most disputes are winnable. Keep fulfillment webhook for paper trail. |
| Architect persona overlap with real estate | Med | Low | DXF + GeoJSON full-dataset is differentiated enough — only architects / surveyors need it. Real-estate devs use the free filtered/viewport scope. |