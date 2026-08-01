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

# 1. Pull fresh snapshots from every public source we already ship from.
log "fetching properties"
python3 -m tools.fetch_properties --portal infocasas  --output-dir "$WORK/infocasas"  || log "WARN infocasas fetch failed"
python3 -m tools.fetch_tulugar    --output-dir "$WORK/tulugar"                          || log "WARN tulugar fetch failed"
python3 -m tools.fetch_clasipar_sitemap --output-dir "$WORK/clasipar"                 || log "WARN clasipar fetch failed"
python3 -m tools.fetch_clasipar_public --output-dir "$WORK/clasipar_v2"               || log "WARN clasipar public fetch failed"

# 2. Merge per-source snapshots into the canonical artifact.
log "merging"
python3 -m scripts.merge_property_sources \
    --inputs "$WORK" \
    --output "$ROOT/data/properties/properties_fresh.geojson"

# 3. Canonicalize (deptos, areas, currency, features, dedupe, freshness).
log "canonicalize"
python3 -m tools.canonicalize_properties \
    --input "$ROOT/data/properties/properties_fresh.geojson" \
    --output "$ROOT/data/properties"

# 4. Build the facets artifact for the viewer.
log "facets"
python3 -m tools.build_facets

# 5. Diff against last deployed artifact; abort if size shrank >30%.
log "diff vs deployed"
python3 -m tools.detect_regression \
    --current "$ROOT/data/properties/canonical_properties.geojson" \
    --last    "$ROOT/exports/web/data/properties_latest.geojson" \
    --max-shrink-pct 30 || {
        log "ABORT regression detected"
        exit 2
    }

# 6. Atomic swap + Pages deploy.
log "deploy"
cp "$ROOT/data/properties/canonical_properties.geojson" \
   "$ROOT/exports/web/data/properties_latest.geojson"
cp "$ROOT/data/properties/facets.json" \
   "$ROOT/exports/web/data/facets.json"
python3 -m tools.build_data_freshness

# 7. Phase C artifacts (cheap, no network).
log "fair-price + image-dedup (mock) + inbio strip"
python3 -m tools.build_fair_price_model_v2 || log "WARN fair-price v2 failed"
python3 -m tools.image_dedup --mock --max-rows 100 || log "WARN image_dedup mock failed"
python3 -m scripts.build_inbio_zafra_strip || log "WARN inbio strip failed"

# 8. Refresh the deployed viewer (overwrite the small artifacts).
[ -f "$ROOT/data/properties/fair_price_model_v2.json" ] && \
    cp "$ROOT/data/properties/fair_price_model_v2.json" \
       "$ROOT/exports/web/data/ml/fair_price_model_v2.json"
[ -f "$ROOT/data/properties/image_clusters.json" ] && \
    cp "$ROOT/data/properties/image_clusters.json" \
       "$ROOT/exports/web/data/image_clusters.json"
[ -f "$ROOT/exports/web/data/inbio_zafra_strip.json" ] || true

"$ROOT/exports/web/wrangler-pages-deploy.sh"

log "done"