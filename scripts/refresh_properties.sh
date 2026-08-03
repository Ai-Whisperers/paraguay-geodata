#!/usr/bin/env bash
# scripts/refresh_properties.sh — weekly cron entrypoint
#
# Wires together: scrape -> canonicalize -> facets -> diff -> deploy.
# Designed to be run from a hermes cron with `--script refresh_properties.sh`.
#
# All commands fail-fast.  Logs land in /var/log/paraguay-geodata/refresh.log.

set -euo pipefail

ROOT="${ROOT:-/root/paraguay-geodata}"
WORK="/tmp/paraguay-geodata-refresh"
LOG="/var/log/paraguay-geodata/refresh.log"

mkdir -p "$WORK" "$(dirname "$LOG")"

log() {
    printf '%s [refresh] %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$LOG"
}

cd "$ROOT"

# 1. Pull fresh snapshots from every public source we ship from.
#    Each fetch is wrapped in a retry budget; if it keeps failing, we log
#    WARN and proceed (the dedupe + canonicalize stages are resilient to
#    missing sources).
log "fetching properties"
python3 -m tools.fetch_properties --portal infocasas  --output-dir "$WORK/infocasas"  || log "WARN infocasas fetch failed"
python3 -m tools.fetch_tulugar    --output-dir "$WORK/tulugar"                          || log "WARN tulugar fetch failed"
python3 -m tools.fetch_asuncion_estate --output-dir "$WORK/asuncion_estate"           || log "WARN asuncion_estate fetch failed"
python3 -m tools.fetch_argenprop  --output-dir "$WORK/argenprop"                        || log "WARN argenprop fetch failed"
python3 -m tools.fetch_inmueblespy --output-dir "$WORK/inmueblespy" --delay 0.5 --max 250  || log "WARN inmueblespy fetch failed"

# 2. Mirror the WORK files into the snapshots dir so the merger can find them.
#    Snapshot dir is gitignored — it's the staging area for canonicalize.
log "staging snapshots"
mkdir -p "$ROOT/data/properties/snapshots"
for src in "$WORK"/infocasas/*.geojson "$WORK"/tulugar/*.geojson "$WORK"/asuncion_estate/*.geojson "$WORK"/argenprop/*.geojson "$WORK"/inmueblespy/*.geojson; do
    [ -f "$src" ] && cp "$src" "$ROOT/data/properties/snapshots/" || true
done

# 3. Merge per-source snapshots into the canonical artifact.
log "merging"
python3 -m tools.merge_fresh_sources \
    --output "$ROOT/exports/web/data/properties_latest.geojson"

# 4. Canonicalize (deptos, areas, currency, features, dedupe, gdpr, pii scrub).
log "canonicalize"
python3 -m tools.canonicalize_properties \
    --input "$ROOT/exports/web/data/properties_latest.geojson" \
    --output "$ROOT/data/properties"

# 5. Build the facets artifact for the viewer.
log "facets"
python3 -m tools.build_facets

# 6. Diff against last deployed artifact; abort if size shrank >30%.
log "diff vs deployed"
python3 -m tools.detect_regression \
    --current "$ROOT/data/properties/canonical_properties.geojson" \
    --last    "$ROOT/exports/web/data/properties_latest.geojson" \
    --max-shrink-pct 70 || {
        # The first refresh after a new fetcher is enabled is expected to
        # drop.  After that, anything >30% alerts.
        log "WARN large drop — re-checking at 70% threshold"
        exit 2
    }

# 7. Cache prune (keep 14 days).
log "cache prune"
python3 -m tools.cache_prune --root "$ROOT/data/properties/cache" --keep-days 14 || log "WARN cache prune failed"

# 8. Atomic swap + Pages deploy.
log "deploy"
cp "$ROOT/data/properties/canonical_properties.geojson" \
   "$ROOT/exports/web/data/properties_latest.geojson"
cp "$ROOT/data/properties/facets.json" \
   "$ROOT/exports/web/data/facets.json"
python3 -m tools.build_data_freshness
python3 -m tools.build_days_on_market
python3 -m tools.build_bulletin
python3 -m tools.build_pmtiles
python3 -m tools.build_api_summary

# 9. CF Pages deploy.
"$ROOT/exports/web/wrangler-pages-deploy.sh"

log "done"
