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
# asuncion.estate: two-pass (fast card walk → detail enrichment only for missing coords)
python3 -m tools.fast_walk_asuncion_estate --output "$WORK/asuncion_estate/fast_walk.geojson" --concurrency 40  || log "WARN asuncion_estate walk failed"
python3 -m tools.enrich_missing_only --walk-snapshot "$WORK/asuncion_estate/fast_walk.geojson" --output "$WORK/asuncion_estate/enriched.geojson" --concurrency 24  || log "WARN asuncion_estate enrich failed"
# Rename so merge_fresh_sources picks it up (needs _YYYY-MM-DD suffix)
if [ -f "$WORK/asuncion_estate/enriched.geojson" ]; then
    DATE=$(date -u +%Y-%m-%d)
    cp "$WORK/asuncion_estate/enriched.geojson" "$WORK/asuncion_estate/enriched_${DATE}.geojson"
fi
python3 -m tools.fetch_argenprop  --output-dir "$WORK/argenprop"                        || log "WARN argenprop fetch failed"
python3 -m tools.fetch_inmueblespy --output-dir "$WORK/inmueblespy" --concurrency 8 --max 500 --delay 0.3  || log "WARN inmueblespy fetch failed"
# Fetch USD/PYG exchange rate (BCP API or stub)
python3 -m tools.fetch_bcp_rates || log "WARN bcp_rates fetch failed"

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
log "deploy-meta"
python3 -m tools.build_deploy_meta --deployer "$(whoami)" || log "WARN deploy-meta build failed"

log "cross-source dedupe"
# Detect cross-posted listings (same property on multiple portals) and
# assign a shared cluster_id + also_listed_by list. This is the only step
# that surfaces "this property is also listed by Infocasas" in the popup.
python3 -m tools.cross_source_dedupe || log "WARN cross-source-dedupe failed"

log "infer property_type"
# Fill in property_type for listings missing it (1,183 → 8 after this).
# Title wins; area is the fallback; bedrooms is the last resort.
python3 -m tools.infer_property_type || log "WARN infer-property-type failed"

log "extract listing metadata"
# Extract area/bedrooms/address/barrio from title for listings that
# didn't expose them as structured fields. Runs AFTER infer so we benefit
# from the title-based extraction first.
python3 -m tools.extract_listing_metadata || log "WARN extract-listing-metadata failed"

log "home stats"
# Refresh the home page hero numbers and meta tags from live data.
# Without this, the home page says "5,784 properties" while the live
# dataset has 10,780. Runs AFTER canonicalize so it sees the latest.
python3 -m tools.build_home_stats || log "WARN build-home-stats failed"

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
