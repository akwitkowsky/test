/*
 * Minimal service worker for the Cost of Meeting PWA.
 *
 * Strategy: a tiny app-shell cache so the app launches offline once installed
 * (e.g. on an iPhone home screen). It precaches the navigation entry on install
 * and serves a cache-first response for navigations, falling back to network
 * for everything else. There is no backend, so there's nothing else to sync.
 */
const CACHE = 'meeting-cost-v1';
const SHELL = ['/', '/index.html', '/manifest.webmanifest'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  // App-shell style: try cache first, fall back to network, and cache new
  // same-origin GET responses so subsequent offline launches work.
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request)
        .then((response) => {
          if (
            response &&
            response.status === 200 &&
            new URL(request.url).origin === self.location.origin
          ) {
            const copy = response.clone();
            caches.open(CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => {
          // Offline navigation fallback to the cached app shell.
          if (request.mode === 'navigate') return caches.match('/index.html');
          return undefined;
        });
    })
  );
});
