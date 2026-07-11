#!/bin/bash
# Fetch OSM distritos in Paraguay, segmented per dept to avoid Overpass timeout.
set +e
cd /root/paraguay-geodata
mkdir -p /tmp/pygeodata_logs exports/web/data/admin/distritos_raw

for slug in py-1 py-2 py-3 py-4 py-5 py-6 py-7 py-8 py-9 py-10 py-11 py-12 py-13 py-14 py-15; do
    log="/tmp/pygeodata_logs/distritos_${slug}.log"
    echo "=== ${slug} $(date) ===" > "$log"
    curl -sS -X POST 'https://overpass.kumi.systems/api/interpreter' \
        --data-urlencode 'data=[out:json][timeout:120];rel["admin_level"="6"]["ISO3166-2"="'"${slug^^}"'"];out tags;' \
        -H 'User-Agent: paraguay-geodata/0.1 (Erebus)' \
        -o "exports/web/data/admin/distritos_raw/${slug}.json" \
        -w 'HTTP %{http_code}  size %{size_download}\n' \
        --max-time 150 >> "$log" 2>&1
    sleep 3
done
echo "=== ALL DONE $(date) ==="
ls -la exports/web/data/admin/distritos_raw/ | head -30