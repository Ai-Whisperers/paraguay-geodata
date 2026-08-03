# Paraguay Geodata — Master Improvement Plan (v2.0)

This is the single source of truth for "what we're doing next".
Replaces `docs/PLAN.md` (now empty) and supersedes `docs/ROADMAP.md`
(49 KB of unstructured ideas from the original 2,500-item brainstorm).

Updated: 2026-08-03.

## Quarterly Pacing

| Quarter | Theme | Target |
|---|---|---|
| Q3 2026 (now) | **Trust + Performance** | PII clean, PMTiles, status page, runbook |
| Q4 2026 | **Coverage** | 10K listings, 5 sources, mobile Lighthouse 90+ |
| Q1 2027 | **Monetization** | Stripe API auth, 1 paying customer |
| Q2 2027 | **International** | Multi-locale, B2B reseller API |

## Q3 2026 — Backlog (ranked by impact/effort)

### Quick wins (≤ 1 day)
1. **PII scrub in write chokepoint** ✅ SHIPPED (`canonicalize_properties.py`)
2. **Delete dead fetchers** ✅ SHIPPED (5 fetchers, ~1,200 LOC)
3. **Add `.gitignore` for `data/tiles/`** ✅ SHIPPED
4. **PMTiles for properties** ✅ SHIPPED (411 KB vs 11 MB)
5. **Public status page** ✅ SHIPPED (`/status`)
6. **CI on every PR** ✅ SHIPPED (`.github/workflows/ci.yml`)
7. **Makefile + Dockerfile** ✅ SHIPPED
8. **Runbook + DR plan** ✅ SHIPPED
9. **GDPR / LGPD takedown filter** ✅ SHIPPED
10. **CITATION.cff** ✅ SHIPPED

### Medium (1-3 days)
11. **Lighthouse CI + Web Vitals** — needs API key, runs in CI
12. **Wire `argenprop` into cron** — quick fetch + 20 listings/month
13. **Source-portal registry** ✅ SHIPPED (`data/properties/source_registry.json`)
14. **Cache-prune cron** — automatic cleanup of > 14d old files
15. **Public bulletin endpoint** — `/bulletin.json` with today’s changes
16. **Plausible analytics** — privacy-friendly, no cookies
17. **Sentry error tracking** — needs DSN key
18. **UptimeRobot / BetterStack** — needs API key

### Larger (3-5 days)
19. **`fetch_inmueblespy.py`** — new fetcher, ~1,500 listings/month
20. **Lazy-load the legacy geojson** — keep the eager one + PMTiles default
21. **Drop `widgets.v3.js` legacy widget** —-30 KB HTML
22. **Replace Stripe checkout-worker with real implementation**
23. **Multi-account CF Pages deploy keys** — for DR
24. **R2 mirror cron** — daily

### Larger (1-2 weeks)
25. **Mobile Lighthouse 90+** — refactor inline CSS, lazy-load scripts
26. **Real-time webhook from any source** — needs server-side
27. **Multi-locale: en / es / pt / gn** for all content (not just the 4 keys)
28. **Re-canonicalize the df_data catalogue** — 30+ government sources

### Strategic (1 month+)
29. **Stripe-backed API** — $29 / $99 / $299 tiers
30. **Multi-tenancy** — single instance, multiple customers
31. **International expansion** — Uruguay, Bolivia, Argentina
32. **Government dataset integrations** — Catastro, SEN, BCP, INE

## What we explicitly WON'T do

- ❌ **Real-time scraping** — sources will block us.  Batch every 1-3 days.
- ❌ **Mobile native app** — PWA-only.  iOS/Android native is months.
- ❌ **AI valuation** — the model is R²=0.017.  Stop pretending.
- ❌ **B2B SaaS until we have 1 paying customer** — don't build auth until user pays.
- ❌ **Multi-cloud deploy** — CF Pages is enough.  Adding GCP/Azure multiplies ops surface.

## How to use this doc

If you want to do something:
- Pick an item from the backlog.
- Update its status (`TODO` → `IN PROGRESS` → `DONE`).
- Add a "Resolves #NNN" line if there's an issue.
- Make a PR; CI runs automatically.

If you want to add a new item:
- Add it to the right quarter.
- Score it on impact (1-5) × effort (1-5).
- Skip if score < 6.

## OKR cross-check

See `/STATUS.md` for the source-of-truth KPIs.  Plan items align 1:1
with OKRs:

- O1 (listings) → items 11, 19, 22
- O2 (trust) → items 1, 5, 9, 17, 18
- O3 (performance) → items 4, 11, 20, 21, 25
- O4 (operability) → items 6, 7, 8, 14, 23, 24
- O5 (monetization) → items 22, 29

## Owners

- @Ai-Whisperers (org)
- @ivan (founder)
- @erebus (this AI agent)

If you change anything above, update this doc.
