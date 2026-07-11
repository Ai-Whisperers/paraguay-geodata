#!/bin/bash
# Local smoke test of the viewer before deploy
set +e
cd /root/paraguay-geodata/exports/web

python3 -m http.server 8765 > /tmp/serve.log 2>&1 &
SERVER_PID=$!
sleep 1

echo "---- probe / (index.html) ----"
curl -sS -o /dev/null -w 'status=%{http_code}  size=%{size_download}\n' http://127.0.0.1:8765/

echo "---- probe /mapa.html ----"
curl -sS -o /dev/null -w 'status=%{http_code}  size=%{size_download}\n' http://127.0.0.1:8765/mapa.html

echo "---- probe /data/tile_index.json ----"
curl -sS -o /dev/null -w 'status=%{http_code}  size=%{size_download}\n' http://127.0.0.1:8765/data/tile_index.json

echo "---- probe /data/priority_tiles.json ----"
curl -sS -o /dev/null -w 'status=%{http_code}  size=%{size_download}\n' http://127.0.0.1:8765/data/priority_tiles.json

echo "---- probe /data/deploy-meta.json ----"
curl -sS -o /dev/null -w 'status=%{http_code}  size=%{size_download}\n' http://127.0.0.1:8765/data/deploy-meta.json

echo "---- probe /mapa.html?tile=-57.069_-25.595 ----"
curl -sS -o /dev/null -w 'status=%{http_code}\n' 'http://127.0.0.1:8765/mapa.html?tile=-57.069_-25.595'

echo "---- HTML content sanity (does it contain Paraguay and Leaflet?) ----"
curl -sS http://127.0.0.1:8765/ | grep -c 'Paraguay'
curl -sS http://127.0.0.1:8765/mapa.html | grep -c 'leaflet'

echo "---- JS sample (first 200 bytes of bootstrap() from index) ----"
curl -sS http://127.0.0.1:8765/ | grep -A 2 'async function bootstrap' | head -3

kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
echo "---- done ----"