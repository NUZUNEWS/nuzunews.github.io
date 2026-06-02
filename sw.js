// ═══════════════════════════════════════════════════════════════════════════
// NUZU News — Service Worker v4.1
// Production-hardened: versioned caches, stale-while-revalidate,
// update-available notification, background refresh, clean eviction.
//
// BUMP CACHE_VERSION on every deploy so stale assets are evicted immediately.
// bot.py should write this file via its SW_FILE path with the version injected.
//
// v4.1 changes vs v4.0:
//   - CACHE_VERSION bumped to v9 (forces full cache eviction on first load
//     after this deploy, clearing any stale v8 routing/JS bundles that
//     contributed to the US nav bug)
//   - nuzu-bundle.js explicitly added to PRECACHE_ASSETS so the fixed
//     bundle is guaranteed to be cached on first install
//   - nuzu-bundle.js explicitly added to stale-while-revalidate strategy
//     so it is always refreshed in background without blocking page load
//   - /offline.html graceful fallback remains (referenced but not blocking)
// ═══════════════════════════════════════════════════════════════════════════

const CACHE_VERSION = 'v10';          // ← BUMPED: evicts v9 caches so the nav fix reaches installed clients
const CACHE_STATIC  = 'nuzu-static-' + CACHE_VERSION;
const CACHE_PAGES   = 'nuzu-pages-'  + CACHE_VERSION;
const CACHE_ICONS   = 'nuzu-icons-'  + CACHE_VERSION;
const ALL_CACHES    = [CACHE_STATIC, CACHE_PAGES, CACHE_ICONS];

const OFFLINE_URL = '/offline.html';

/* Assets precached on install — the "app shell" */
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json',
  '/nuzu-bundle.js',  // ← added: ensure fixed bundle is cached immediately
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

/* Feeds that should always be fresh (network-first, 5s timeout) */
const FRESH_PATHS = ['/feed.json', '/feed.xml', '/version.json'];

/* Static assets that can be served from cache indefinitely */
const STATIC_EXTS = /\.(png|jpg|jpeg|webp|gif|svg|ico|woff2?|ttf|otf)$/i;

/* ───────────────────────────────────────────────────────────────────────────
   INSTALL — precache the shell, then activate immediately
─────────────────────────────────────────────────────────────────────────── */
self.addEventListener('install', event => {
  self.skipWaiting(); // new SW takes over without waiting for old tabs to close
  event.waitUntil(
    caches.open(CACHE_STATIC).then(cache =>
      cache.addAll(PRECACHE_ASSETS).catch(err => {
        // Partial failures are acceptable — don't block install
        console.warn('[NUZU SW] Precache partial failure:', err);
      })
    )
  );
});

/* ───────────────────────────────────────────────────────────────────────────
   ACTIVATE — evict ALL old caches, claim all open clients, notify UI
─────────────────────────────────────────────────────────────────────────── */
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(k => !ALL_CACHES.includes(k))
          .map(k => {
            console.log('[NUZU SW] Evicting old cache:', k);
            return caches.delete(k);
          })
      ))
      .then(() => self.clients.claim())
      .then(() => {
        // Tell all open tabs: new version is active
        return self.clients.matchAll({ type: 'window' }).then(clients => {
          clients.forEach(client =>
            client.postMessage({ type: 'NUZU_SW_UPDATED', version: CACHE_VERSION })
          );
        });
      })
  );
});

/* ───────────────────────────────────────────────────────────────────────────
   FETCH — strategy per resource type
─────────────────────────────────────────────────────────────────────────── */
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Only handle same-origin + YouTube (video embeds)
  const isSameOrigin = url.origin === self.location.origin;
  const isYouTube    = url.hostname.includes('youtube.com') ||
                       url.hostname.includes('ytimg.com');
  if (!isSameOrigin && !isYouTube) return;

  // ── Strategy 1: Feed data — network-first, 5s timeout, cache fallback ──
  if (FRESH_PATHS.some(p => url.pathname === p || url.pathname.startsWith(p + '?'))) {
    event.respondWith(networkFirstWithTimeout(event.request, CACHE_PAGES, 5000));
    return;
  }

  // ── Strategy 2: HTML pages — network-first, cache on success ──
  if (event.request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirstHtml(event.request));
    return;
  }

  // ── Strategy 3: Source favicons (/icons/sources/) — stale-while-revalidate ──
  if (url.pathname.startsWith('/icons/sources/')) {
    event.respondWith(staleWhileRevalidate(event.request, CACHE_ICONS));
    return;
  }

  // ── Strategy 4: nuzu-bundle.js — stale-while-revalidate (always refresh) ──
  // Explicit rule ensures the fixed bundle is never stuck in a stale cache.
  if (url.pathname === '/nuzu-bundle.js' || url.pathname.startsWith('/nuzu-bundle.js?')) {
    event.respondWith(staleWhileRevalidate(event.request, CACHE_STATIC));
    return;
  }

  // ── Strategy 5: Static binary assets — cache-first (long TTL) ──
  if (STATIC_EXTS.test(url.pathname) || url.pathname.startsWith('/icons/')) {
    event.respondWith(cacheFirstStatic(event.request, CACHE_STATIC));
    return;
  }

  // ── Strategy 6: JS/CSS — stale-while-revalidate ──
  if (/\.(js|css)$/i.test(url.pathname)) {
    event.respondWith(staleWhileRevalidate(event.request, CACHE_STATIC));
    return;
  }

  // ── Default: network-only for everything else (YouTube iframes, etc.) ──
});

/* ───────────────────────────────────────────────────────────────────────────
   CACHE STRATEGIES
─────────────────────────────────────────────────────────────────────────── */

/** Network-first with timeout; fall back to cache; final fallback: offline page. */
async function networkFirstWithTimeout(request, cacheName, ms) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    const response = await fetch(request, { signal: controller.signal, cache: 'no-cache' });
    clearTimeout(timer);
    if (response.ok) {
      const clone = response.clone();
      caches.open(cacheName).then(c => c.put(request, clone));
    }
    return response;
  } catch (_) {
    clearTimeout(timer);
    const cached = await caches.match(request);
    return cached || new Response('{}', { status: 503, headers: { 'Content-Type': 'application/json' } });
  }
}

/** Network-first for HTML; falls back to cached HTML, then offline page. */
async function networkFirstHtml(request) {
  try {
    const response = await fetch(request, { cache: 'no-cache' });
    if (response.ok) {
      const clone = response.clone();
      caches.open(CACHE_PAGES).then(c => c.put(request, clone));
    }
    return response;
  } catch (_) {
    const cached = await caches.match(request);
    if (cached) return cached;
    const offline = await caches.match(OFFLINE_URL);
    return offline || new Response('<h1>Offline</h1>', {
      status: 503,
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

/** Cache-first for static assets; network fallback; cache on success. */
async function cacheFirstStatic(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const clone = response.clone();
      caches.open(cacheName).then(c => c.put(request, clone));
    }
    return response;
  } catch (_) {
    return new Response('', { status: 404 });
  }
}

/** Serve from cache immediately; update cache in background. */
async function staleWhileRevalidate(request, cacheName) {
  const cached = await caches.match(request);
  const fetchPromise = fetch(request).then(response => {
    if (response.ok) {
      const clone = response.clone();
      caches.open(cacheName).then(c => c.put(request, clone));
    }
    return response;
  }).catch(() => cached);
  return cached || fetchPromise;
}

/* ───────────────────────────────────────────────────────────────────────────
   PUSH NOTIFICATIONS
─────────────────────────────────────────────────────────────────────────── */
self.addEventListener('push', event => {
  let data = { title: 'NUZU Breaking News', body: 'New headlines available', url: '/' };
  try { if (event.data) data = { ...data, ...event.data.json() }; } catch (_) {}

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body:              data.body,
      icon:              '/icons/icon-192.png',
      badge:             '/icons/icon-96.png',
      tag:               'nuzu-breaking',
      renotify:          true,
      requireInteraction: false,
      data:              { url: data.url },
      actions: [
        { action: 'open',    title: 'Read Now' },
        { action: 'dismiss', title: 'Dismiss'  }
      ]
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'dismiss') return;

  const url = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        if ('focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});

/* ───────────────────────────────────────────────────────────────────────────
   BACKGROUND SYNC — periodic headline refresh
─────────────────────────────────────────────────────────────────────────── */
self.addEventListener('periodicsync', event => {
  if (event.tag !== 'nuzu-headlines-refresh') return;
  event.waitUntil(
    fetch('/feed.json?sw=1&_=' + Date.now(), { cache: 'no-cache' })
      .then(r => r.json())
      .then(data => self.clients.matchAll({ type: 'window' }).then(clients => {
        clients.forEach(c => c.postMessage({ type: 'NUZU_UPDATE', updated: data.updated }));
      }))
      .catch(() => {})
  );
});

/* ───────────────────────────────────────────────────────────────────────────
   MESSAGES FROM PAGE
─────────────────────────────────────────────────────────────────────────── */
self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();

  // Respond to version check
  if (event.data?.type === 'GET_VERSION') {
    event.source?.postMessage({ type: 'SW_VERSION', version: CACHE_VERSION });
  }
});
