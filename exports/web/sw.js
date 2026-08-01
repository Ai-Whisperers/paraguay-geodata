// Service Worker — Paraguay Geodata PWA
// Cache-first for static assets, stale-while-revalidate for data
// Robust against CSP-blocked fetches, offline mode
const CACHE_NAME = 'paraguay-geodata-v10';  // bumped 2026-08-01 — secondary-insights (days-on-market + mortgage) widgets + canonical 17-depto facets + filter UI (depto/source/hide-flagged/has-images) + cross-source dedupe popups + quality flags panel

// On-install: precache critical same-origin assets only
// CDN assets (Leaflet, Inter font) are cached on first fetch, not on install
// (avoids CSP-blocked install + faster startup)
const STATIC_CACHE = [
    './',
    './manifest.webmanifest',
    './sw.js',
    './data/data_freshness.json',
    './data/deploy-meta.json',
    './data/tile_index.json',
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) =>
            // Best-effort — install succeeds even if some fail
            Promise.allSettled(STATIC_CACHE.map((url) =>
                cache.add(url).catch(() => null)
            ))
        ).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keys) => Promise.all(
            keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
        )).then(() => self.clients.claim())
    );
});

// Helper: build a safe Response (avoid "Failed to convert" errors)
const safeResponse = (body, init = {}) => {
    try {
        return new Response(body, init);
    } catch (e) {
        return new Response('', { status: 504, statusText: 'Offline' });
    }
};

self.addEventListener('fetch', (e) => {
    const url = new URL(e.request.url);

    // Skip non-GET, browser-extension, geocoder
    if (e.request.method !== 'GET') return;
    if (url.protocol === 'chrome-extension:') return;
    if (url.protocol === 'moz-extension:') return;
    if (url.host === 'photon.komoot.io') return; // network-only (POST)

    // Determine resource type
    const isSameOrigin = url.origin === self.location.origin;
    const isStatic = /\.(css|js|woff2?|png|svg|ico|webmanifest|json)$/.test(url.pathname);
    const isData = url.pathname.startsWith('/data/');

    // Same-origin static + data: cache-first / SWR
    if (isSameOrigin && (isStatic || isData)) {
        e.respondWith(
            caches.open(CACHE_NAME).then((cache) =>
                cache.match(e.request).then((cached) => {
                    const fetchAndCache = fetch(e.request).then((r) => {
                        if (r.ok) cache.put(e.request, r.clone()).catch(() => {});
                        return r;
                    }).catch(() => {
                        // Network failed → return cache or fallback
                        if (cached) return cached;
                        return safeResponse('', { status: 504 });
                    });
                    // Stale-while-revalidate for data, cache-first for static
                    return cached || fetchAndCache;
                })
            )
        );
        return;
    }

    // Cross-origin (CDN: Leaflet, Inter font, etc.): network with cache fallback
    if (!isSameOrigin) {
        e.respondWith(
            caches.match(e.request).then((cached) => {
                if (cached) return cached;
                return fetch(e.request).then((r) => {
                    if (r.ok) {
                        const clone = r.clone();
                        caches.open(CACHE_NAME).then((c) => c.put(e.request, clone).catch(() => {}));
                    }
                    return r;
                }).catch(() => safeResponse('', { status: 504 }));
            })
        );
        return;
    }

    // Default: pass through
    e.respondWith(fetch(e.request).catch(() => safeResponse('', { status: 504 })));
});

// Allow page to skip waiting on update
self.addEventListener('message', (e) => {
    if (e.data === 'skipWaiting') self.skipWaiting();
});