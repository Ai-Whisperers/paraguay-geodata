#!/bin/bash
# Big crawl: all 17 deptos × 2 pages each
# Designed to be robust to PG/agent pulls (set +e everywhere)
cd /root/paraguay-geodata
mkdir -p /tmp/pygeodata_logs
echo "BIG_CRAWL_START $(date)" > /tmp/pygeodata_logs/big_crawl.log

for slug in asuncion central alto-parana concepcion san-pedro cordillera guaira caaguazu caazapa itapua misiones paraguari neembucu amambay canindeyu presidente-hayes boqueron alto-paraguay; do
    log="/tmp/pygeodata_logs/${slug}.log"
    echo "=== DEPT=$slug ===" >> "$log"
    python3 -m tools.fetch_properties --portal infocasas --max-pages 2 --dept "$slug" >> "$log" 2>&1 || true
    echo "  -- DONE $slug $(date)" >> /tmp/pygeodata_logs/big_crawl.log
done
echo "=== ALL DEPTOS DONE $(date) ===" >> /tmp/pygeodata_logs/big_crawl.log
cp -f exports/web/data/properties_latest.geojson exports/web/data/properties_countrywide_$(date +%Y-%m-%d_%H%M).geojson
echo "FINAL_LISTING_COUNT" >> /tmp/pygeodata_logs/big_crawl.log
python3 -c "import json; d=json.load(open('exports/web/data/properties_latest.geojson')); print(f'features={len(d[\"features\"])}', file=open('/tmp/pygeodata_logs/big_crawl.log','a'))"