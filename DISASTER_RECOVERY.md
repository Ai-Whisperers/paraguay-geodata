# Paraguay Geodata — Disaster Recovery Plan

What's the worst case, and how do we recover.

## Threat model

| Threat | Likelihood | Impact | Recovery |
|---|---|---|---|
| GitHub account compromised | Low | Medium | Rotate tokens, force-push to revert |
| Cloudflare account compromised | Low | High | Use Wrangler CLI alternative deploy |
| R2 / wrangler storage lost | Very low | High | Re-run pipeline from `git clone` |
| Repo deleted | Very low | Critical | Restore from GitHub backup or fork |
| Iván unavailable (bus factor 1) | Medium | High | Anyone with cloudflare token can deploy |
| Source portals (InfoCasas, TuLugar, AE) block us | Medium | Medium | Hit scrape-ethics policy; back off |
| Scraper accidentally publishes PII | Low | High | Roll back + patch `scrub_pii.py` |
| Stripe account compromised | Medium | High | Rotate keys; notify customers |
| DB / data leak | Low | Critical | All data is CC0 except emails (none stored) |

## Recovery time objectives

- **Full site restore:** 1 hour (assuming git + CF tokens available)
- **Data pipeline rebuild:** 4 hours (re-pull from sources)
- **Cold start from nothing:** 8 hours (clone repo, install deps, fetch all)

## What we recover from

1. **GitHub repo** is the source of truth for code.  Tarball is at
   https://github.com/Ai-Whisperers/paraguay-geodata/archive/refs/heads/main.tar.gz
2. **Cloudflare Pages** is the source of truth for the live site.  We can
   inspect deployment history at any time.
3. **Hugging Face / S3** mirror (TBD — not yet implemented).  See Wave 5 below.

## Steps to fully recover from total loss

```bash
# 1. Clone the repo
git clone https://github.com/Ai-Whisperers/paraguay-geodata
cd paraguay-geodata

# 2. Install dependencies
make install-dev

# 3. (Optional) Build all data from scratch
# This is the slow path — ~4 hours for the full pipeline.
make fetch-all build-all

# 4. Deploy to Cloudflare Pages
export CLOUDFLARE_API_TOKEN=...
export CLOUDFLARE_ACCOUNT_ID=...
make deploy-prod
```

The first deploy will be slightly stale (~3 days, the last cron run).  After
the first deploy, the cron resumes automatically.

## Cron failure cascade

If the cron fails for > 7 days, the data is stale.  The site still serves
the last good snapshot.  Recovery is identical to "data pipeline rebuild"
above.

## Domain loss

If `geodata.paragu-ai.com` is lost:

1. Buy a backup domain (e.g., `paraguay-geodata.pages.dev` — already pinned).
2. Update `_redirects` to canonicalize.
3. Update `canonical` URLs in `<head>` and `sitemap.xml`.

CF Pages already gives us `paraguay-geodata.pages.dev` automatically.

## Secrets loss

| Secret | Where it's used | Recovery |
|---|---|---|
| `CLOUDFLARE_API_TOKEN` | wrangler deploy | Rotate in CF dashboard, push to Hermes cron |
| `CLOUDFLARE_ACCOUNT_ID` | wrangler deploy | Same |
| `GITHUB_TOKEN` | CI | GitHub → Settings → tokens |
| Stripe (none yet) | checkout-worker | n/a |

If a secret is leaked (e.g., found in a public file), rotate immediately.

## Data backup

As of 2026-08-03, the canonical geojson is committed to git.  If we
lose git, we lose the historical record.  A future improvement is
to dump the canonical artifact to R2 hourly.

Proposed R2 layout:
```
paraguay-geodata/
  canonical_properties.geojson      # latest
  snapshots/2026-08-03/properties.geojson
  snapshots/2026-08-04/properties.geojson
  ...
```

## Scenario walkthroughs

### Scenario 1: Iván is away for a week

The cron keeps running.  The site keeps updating.  Anyone with the CF
token can deploy.  No action needed.

### Scenario 2: InfoCasas aggressively blocks our IP

Backoff: stop the cron for 3 days.  Py will resume.  Meanwhile, the
asuncion_estate + tulugar sources still feed.

### Scenario 3: A listing is wrong and the source portal won't fix it

Manual: add `source_url` to `data/properties/deleted_listings.json`.
Re-run canonicalize.  The listing disappears.

### Scenario 4: Cloudflare Pages has 100% outage

We have no fall-back.  The site is offline.  DOC this in the `README.md`.

### Scenario 5: We accidentally publish a private dataset

Roll back to the last clean commit.  Patch the pipeline to prevent
re-publish.  Send a takedown notice if needed.

### Scenario 6: AI-generated content is bad

The site has a feedback button (mailto:erebus@ai-whisperers.org).  All
complaints are manually reviewed.  Spam is filtered.

### Scenario 7: We get a legal threat

Forward to legal@ai-whisperers.org.  Lawful response within 30 days.
If the claim is valid, remove the listing.

### Scenario 8: A user requests data deletion

See RUNBOOK.md → "Takedown request received".

## What we still need

- [ ] S3/R2 mirror (hourly)
- [ ] Wrangler Tail alerting
- [ ] GitHub branch protection on main
- [ ] Multi-account CF Pages deploy keys
- [ ] Off-boarded source-portal rate-limit visibility
- [ ] Stripe-integrated customer portal (we have no customers yet)

## Owners

- @Ai-Whisperers (org)
- @ivan (founder)
- @erebus (this AI agent)

If you change anything above, update this doc.
