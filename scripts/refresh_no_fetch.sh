#!/usr/bin/env bash
# scripts/refresh_no_fetch.sh — daily cron entrypoint
#
# Same as refresh_properties.sh but skips the fetchers (they're weekly).
# Catches weekday drift by rebuilding canonical/facets/bulletin/pmtiles
# and deploying the artifacts.
#
# Designed to be run from a Linux cron with:
#   30 8 * * * bash /root/paraguay-geodata/scripts/refresh_no_fetch.sh >> /var/log/paraguay-geodata/refresh.log 2>&1

set -euo pipefail

ROOT="${ROOT:-/root/paraguay-geodata}"
LOG="/var/log/paraguay-geodata/refresh.log"

mkdir -p "$(dirname "$LOG")"

log() {
    printf '%s [refresh-no-fetch] %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$LOG"
}

cd "$ROOT"

log "canonicalize"
python3 -m tools.canonicalize_properties \
    --input "$ROOT/exports/web/data/properties_latest.geojson" \
    --output "$ROOT/data/properties"

log "swap canonical"
cp "$ROOT/data/properties/canonical_properties.geojson" \
   "$ROOT/exports/web/data/properties_latest.geojson"

log "facets"
python3 -m tools.build_facets

log "freshness"
python3 -m tools.build_data_freshness

log "days-on-market"
python3 -m tools.build_days_on_market

log "bulletin"
python3 -m tools.build_bulletin

log "pmtiles"
python3 -m tools.build_pmtiles

log "api summary"
python3 -m tools.build_api_summary

log "vitals summary"
python3 -m tools.webhook_ingest --summarize || log "WARN webhook_ingest failed"

log "cache prune"
python3 -m tools.cache_prune --root "$ROOT/data/properties/cache" --keep-days 14 \
    || log "WARN cache prune failed"

log "deploy"
"$ROOT/exports/web/wrangler-pages-deploy.sh"

log "done"
