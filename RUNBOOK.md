# Paraguay Geodata — Operational Runbook

This is the playbook for keeping the site live.  Read it before paging.

## TL;DR

- **Live at:** https://geodata.paragu-ai.com/ (Cloudflare Pages)
- **Source:** https://github.com/Ai-Whisperers/paraguay-geodata
- **Owner:** @Ai-Whisperers
- **Critical files:** `exports/web/` (deployed), `tools/` (data pipeline), `data/properties/` (snapshot state)

## Daily operations

### Cron (every 1–3 days)

`scripts/refresh_properties.sh` → runs `fetch_tulugar`, `fetch_asuncion_estate`,
`fetch_properties --portal infocasas`, `merge_fresh_sources`, `build_facets`,
`build_data_freshness`, `build_days_on_market`, `wrangler pages deploy`.

After each run, verify:

```bash
# 1. Latest deploy is live
curl -sI https://geodata.paragu-ai.com/ | head -3

# 2. Properties counted
curl -s https://geodata.paragu-ai.com/api/v1/properties.json | python3 -c "import json,sys; print(json.load(sys.stdin)['total'])"

# 3. PII is clean
python3 -m pytest tests/test_pii_scrub.py -v --no-header

# 4. Tests pass
make test
```

### Manual refresh

```bash
make fetch-all build-all deploy-prod
```

## Common failures

### A) CF Pages shows 404

1. Check last deploy: `wrangler pages deployment list --project-name paraguay-geodata`
2. If the failure was a manual revert, redeploy: `make deploy-prod`
3. If the failure was a scaling event, wait 5 min and verify.

### B) Source scraper 403 / 429

Usually Cloudflare blocking our IP.  Wait 30 min, then:

```bash
make fetch-infocasas
```

If persistent, reduce `--max-pages` or add a new proxy.

### C) PII scrub fails

1. Run `pytest -v tests/test_pii_scrub.py`.
2. If `n_violations > 0`, the public geojson still has real phones.  DO NOT DEPLOY.
3. Check `data/properties/canonical_properties.geojson` for the offending text.
4. Add a `PHONE_RE` variant to `tools/scrub_pii.py` until the scrub catches it.
5. Re-run `make canonicalize` and verify.

### D) Index.html > 350 KB

The legacy map widget is bloating.  Check `git diff exports/web/`.
Revert to last known-good:

```bash
git checkout HEAD~1 -- exports/web/index.html
make deploy-prod
```

### E) Cloudflare Pages is down

1. Status: https://www.cloudflarestatus.com/
2. If persistent, point a CNAME to a backup (we don't have one — see ARCHITECTURE.md for "DR plan").

### F) Data divergence (catalog suddenly drops)

```bash
# Compare current vs last-known-good
git diff HEAD~1 -- exports/web/data/properties_latest.geojson | head -50
```

If a single source dropped, check the cron logs.  If all sources dropped,
likely a connectivity issue.

### G) GitHub Actions failing

1. Check the run: https://github.com/Ai-Whisperers/paraguay-geodata/actions
2. Most failures are: pre-commit timeout, pytest timing out (>12 min), or wrangler auth.
3. Re-run after fixing the cause.

### H) Stripe webhook failing

We have NO live Stripe integration.  This is a `TODO`.  If you see webhook errors:
check `exports/checkout-worker/` is not actually deployed.

### I) Takedown request received (GDPR / LGPD)

1. Open `data/properties/deleted_listings.json`.
2. Add `{"source_url": "...", "added_at": "..."}`.
3. Re-run `make canonicalize merge build-all deploy-prod`.
4. Confirm with the requester.

### J) Bus factor 1 (Iván is unreachable)

1. Anyone with CLOUDFLARE_API_TOKEN can deploy.
2. Anyone with GitHub admin can approve.
3. The repo, the data, and the cron tokens are documented; see **DISASTER_RECOVERY.md**.

### K) Fair-price model behaving badly

The model is **EXPERIMENTAL** with R² ≈ 0.017 and is labeled as such in
`exports/web/data/ml/fair_price_model_v2.json`.  If users complain:
disable the model entirely by setting `disclosure.disabled = true`.

### L) Site suddenly slow

1. Check CF analytics: https://radar.cloudflare.com/
2. Check `_redirects` for any accidental loops (we hit one in Aug 2026).
3. Check `data/properties/canonical_properties.geojson` size — if it grew
   beyond 30 MB, the cache prune cron is broken.

## Recovery

### Rollback a deploy

```bash
# Find the previous successful deployment
wrangler pages deployment list --project-name paraguay-geodata | head -20

# Find the commit hash that deployed
git log --oneline --grep='feat' | head -10

# Re-deploy the previous commit
git checkout <hash> -- exports/web/
make deploy-prod
git checkout main -- exports/web/
```

### Restore from backup

We don't have off-site backups.  The git history is the backup.  If
git is gone too, see **DISASTER_RECOVERY.md**.

### Lift a property ban

If you accidentally deleted a listing from `data/properties/deleted_listings.json`:
remove the entry, redeploy.  The next cron will re-fetch the source and
re-add it.

## Logging

Currently no centralized logging.  Until then:

- `make fetch-X` prints to stdout
- `pytest -v` for test failures
- `git log -- exports/web/` for which deploys changed what
- `wrangler tail --project-name paraguay-geodata` for live traffic logs

## Owners

- @Ai-Whisperers (org)
- @ivan (founder)
- @erebus (this AI agent)

If you change anything above, update this doc.
