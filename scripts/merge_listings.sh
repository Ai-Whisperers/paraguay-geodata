#!/bin/bash
# Re-crawl all deptos + merge into one national file.
# Usage: bash scripts/merge_listings.sh [--full]
set -e
cd /root/paraguay-geodata
mkdir -p /tmp/pygeodata_logs

SLUGS=(asuncion central alto-parana concepcion san-pedro cordillera guaira caaguazu caazapa itapua misiones paraguari neembucu amambay canindeyu presidente-hayes boqueron alto-paraguay)

# Cache clear so each dept actually fetches new listings (don't accumulate cache hits)
rm -rf data/properties/cache/infocasas/

total_start=$(date +%s)
for slug in "${SLUGS[@]}"; do
    log="/tmp/pygeodata_logs/${slug}.log"
    [ -f "$log" ] && rm -f "$log"
    echo "=== START dept=$slug $(date +%T) ===" >> /tmp/pygeodata_logs/merge.log
    python3 -m tools.fetch_properties --portal infocasas --max-pages 2 --dept "$slug" >> "$log" 2>&1 || true
    echo "=== DONE dept=$slug $(date +%T) ===" >> /tmp/pygeodata_logs/merge.log
done

# Build a national GeoJSON by concatenating per-department snapshots + dedup
python3 - << 'PYEOF'
import json, glob, re
from collections import OrderedDict

snap_dir = '/root/paraguay-geodata/data/properties/snapshots/'
out = {'type':'FeatureCollection','features':[]}
seen = OrderedDict()
snap_files = sorted(glob.glob(snap_dir + '*.geojson'))
print(f"Merging {len(snap_files)} snapshots...", flush=True)

# Walk from latest run + use the most recent all_*.geojson which is the latest fetch
import os
latest_snap = max(snap_files, key=os.path.getmtime)
print(f"Latest snap: {latest_snap} ({os.path.getmtime(latest_snap)})", flush=True)
# But for NATIONAL merge, just use the latest per-dept snapshot
for f in snap_files:
    m = re.match(r'.+_(20\d\d-\d\d-\d\d_\d\d\d\d)\.geojson', os.path.basename(f))
    if not m:
        continue
    if m.group(1) != os.path.basename(latest_snap).split('_')[-1].replace('.geojson',''):
        # skip older dates
        pass

# Re-fetch the per-dept one big snapshot: use today's all_*.geojson which is the latest fetch
today_snap = '/root/paraguay-geodata/data/properties/snapshots/all_2026-07-11.geojson'
if os.path.exists(today_snap):
    d = json.load(open(today_snap))
    for rec in d.get('raw_records', []):
        if rec.get('lat') is None:
            continue
        f = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [rec['lon'], rec['lat']]},
            'properties': {k:v for k,v in rec.items() if k not in ('lat','lon')}
        }
        rid = f['properties'].get('id')
        if rid and rid not in seen:
            seen[rid] = True
            out['features'].append(f)
print(f"Merged total: {len(out['features'])} features (dedup by id)")
with open('/root/paraguay-geodata/exports/web/data/properties_latest.geojson','w') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
PYEOF

total_end=$(date +%s)
echo "TOTAL DURATION: $((total_end - total_start)) sec" >> /tmp/pygeodata_logs/merge.log
ls -la exports/web/data/properties_latest.geojson