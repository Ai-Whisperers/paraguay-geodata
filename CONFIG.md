# Paraguay Geodata — Configuration

## Where config lives

| Layer | Where | Scope |
|---|---|---|
| Deploy secrets | `.env` (gitignored) | CI + wrangler |
| Public URLs | `exports/web/_redirects` | CF Pages routing |
| HTTP headers | `exports/web/_headers` | CF Pages CSP, HSTS |
| Source registry | `data/properties/source_registry.json` | Manifest |
| Takedown list | `data/properties/deleted_listings.json` | GDPR / LGPD |
| List of deploy keys | `~/.cloudflare-env` (Hermes cron) | Multi-account |
| Github Actions secrets | repo → Settings → Secrets | CI |

## Multi-account Cloudflare deploy

We have two Cloudflare accounts:

1. **Primary** — production + main branch
2. **Backup** — DR + staging branch (when armed)

When the primary is unreachable, switch to the backup:

```bash
# 1. Switch credentials
export CLOUDFLARE_API_TOKEN=$CLOUDFLARE_API_TOKEN_BACKUP
export CLOUDFLARE_ACCOUNT_ID=$CLOUDFLARE_ACCOUNT_ID_BACKUP

# 2. Push to the staging branch
git push origin feat/backup-deploy:staging

# 3. Deploy to the backup account
make deploy-preview
```

## Sentry / error tracking

If `SENTRY_DSN` is set, the frontend (`exports/web/site.js`) will
initialize Sentry.  Unset to disable.

Self-hosted Sentry: not configured.  We use the SaaS version.

## Uptime monitoring

If `UPTIMEROBOT_API_KEY` is set, `make status` will hit the
UptimeRobot API and surface downtime in the public status page.

We don't yet have a UptimeRobot account.  See `/STATUS.md` Q3 OKR.

## Plausible analytics

If `PLAUSIBLE_DOMAIN` is set, `exports/web/index.html` adds a
single-pixel `https://plausible.io/js/script.js` script tag.

Self-hosted Plausible: not configured.

## Cron path

Hermes cron at `~/.hermes/cron/jobs.json` has the noon-time run.
See RUNBOOK.md for the full cron pattern.

## Debug mode

Set `PY_REFRESH_DRY_RUN=true` to skip all writes (smoke test).
