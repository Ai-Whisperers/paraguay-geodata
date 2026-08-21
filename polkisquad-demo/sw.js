// Polki Squad — service worker
// Caches the site shell + static assets for offline access.

const CACHE_NAME = 'polkisquad-v1';
const RUNTIME_CACHE = 'polkisquad-runtime-v1';
const ASSETS = [
  '/',
  '/404.html',
  '/adopta.html',
  '/animal/bruno.html',
  '/animal/luna.html',
  '/animal/mishi.html',
  '/animal/pelusa.html',
  '/animal/rocky.html',
  '/animal/toby.html',
  '/blog.html',
  '/contacto.html',
  '/css/mobile-nav.css',
  '/css/page-adopta.css',
  '/css/page-animal.css',
  '/css/page-blog.css',
  '/css/page-contacto.css',
  '/css/page-donar.css',
  '/css/page-padrinos.css',
  '/css/page-somos.css',
  '/css/page-voluntarios.css',
  '/css/styles.css',
  '/cuenta-mi-caso.html',
  '/donar.html',
  '/eventos.html',
  '/favicon.ico',
  '/favicon.svg',
  '/for-polkisquad.html',
  '/gracias/donar.html',
  '/gracias/padrino.html',
  '/index.html',
  '/js/main.js',
  '/manifest.json',
  '/og/default.svg',
  '/padrinos.html',
  '/perdidos-y-encontrados.html',
  '/press-kit.html',
  '/privacidad.html',
  '/quienes-somos.html',
  '/sponsors.html',
  '/terminos.html',
  '/transparencia.html',
  '/voluntarios.html'
];

// Install: pre-cache the site shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS).catch((err) => {
        console.warn('[SW] Some assets failed to cache:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  const currentCaches = [CACHE_NAME, RUNTIME_CACHE];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return cacheNames.filter((name) => !currentCaches.includes(name));
    }).then((cachesToDelete) => {
      return Promise.all(cachesToDelete.map((cacheToDelete) => {
        return caches.delete(cacheToDelete);
      }));
    }).then(() => self.clients.claim())
  );
});

// Fetch: cache-first for static, network-first for HTML
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip cross-origin requests (analytics, fonts, etc.)
  if (url.origin !== location.origin) return;

  // For HTML pages: network-first, fall back to cache
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone and cache the response
          const clone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, clone);
          });
          return response;
        })
        .catch(() => {
          // Network failed, try cache
          return caches.match(request).then((cached) => {
            return cached || caches.match('/404.html');
          });
        })
    );
    return;
  }

  // For static assets: cache-first
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        // Cache successful responses
        if (response.ok) {
          const clone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, clone);
          });
        }
        return response;
      });
    })
  );
});
