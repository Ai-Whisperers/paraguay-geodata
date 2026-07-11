// Service Worker — Paraguay Geodata PWA
// Cache-first for static assets, network-first for data
const CACHE_NAME = 'paraguay-geodata-v3';
const STATIC_CACHE = [
    './',
    './manifest.webmanifest',
    './data/properties_latest.geojson',
    './data/roads.geojson',
    './data/buildings_asuncion.geojson',
    './data/water.geojson',
    './data/gbif_paraguay.geojson',
    './data/tile_index.json',
    './data/priority_tiles.json',
    './data/bcp_snapshot.json',
    './data/nasa_power_asuncion.json',
    './data/inbio_zafra_2025_2026.json',
    './data/admin/catastro_dpto.geojson',
    './data/admin/catastro_dist.geojson',
    './data/admin/catastro_parcels_sample.geojson',
    './data/admin/catastro_urba.geojson',
    './data/admin/barrios_py.geojson',
    './data/ml/fair_price_model.json',
    './data/deploy-meta.json',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
    'https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js',
    'https://rsms.me/inter/inter.css',
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            // Best-effort cache; CDN failures don't break install
            return Promise.allSettled(STATIC_CACHE.map((url) =>
                fetch(url).then((r) => r.ok ? cache.put(url, r.clone()) : null).catch(() => null)
            ));
        }).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keys) => Promise.all(
            keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
        )).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (e) => {
    const url = new URL(e.request.url);
    // Skip non-GET, geocoder (POST), chrome-extension
    if (e.request.method !== 'GET') return;
    if (url.protocol === 'chrome-extension:') return;
    if (url.host === 'photon.komoot.io') return; // network only

    // Cache-first for same-origin static, network-first for data
    const isStatic = /\.(css|js|woff2?|png|svg|ico|webmanifest)$/.test(url.pathname);
    const isData = url.pathname.startsWith('/data/');

    if (isStatic) {
        e.respondWith(
            caches.match(e.request).then((cached) => cached || fetch(e.request).then((r) => {
                if (r.ok) {
                    const clone = r.clone();
                    caches.open(CACHE_NAME).then((c) => c.put(e.request, clone));
                }
                return r;
            }).catch(() => cached))
        );
        return;
    }

    if (isData) {
        // Stale-while-revalidate: return cache instantly, refresh in background
        e.respondWith(
            caches.open(CACHE_NAME).then((cache) =>
                cache.match(e.request).then((cached) => {
                    const fetchPromise = fetch(e.request).then((r) => {
                        if (r.ok) cache.put(e.request, r.clone());
                        return r;
                    }).catch(() => cached);
                    return cached || fetchPromise;
                })
            )
        );
        return;
    }

    // Default: network with cache fallback
    e.respondWith(
        fetch(e.request).catch(() => caches.match(e.request))
    );
});