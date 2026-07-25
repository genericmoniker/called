// Service Worker for offline support.

// Note that the first request to the board (or after the CACHE_NAME version changes)
// is what installs the SW, so it won't get cached until the board cycles back around
// to it later with the SW in place.

// Update the version part of the CACHE_NAME string to force clients to update
// their cache when changes are made.
const CACHE_NAME = 'board-v13';


self.addEventListener('install', (event) => {
    event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
    // Delete old caches that don't match the current version and
    // claim clients so that the new SW takes effect immediately.
    event.waitUntil(
        caches.keys()
        .then((cacheNames) => Promise.all(
                cacheNames
                    .filter((cacheName) => cacheName.startsWith('board-') && cacheName !== CACHE_NAME)
                    .map((cacheName) => caches.delete(cacheName))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const request = event.request;
    if (request.method !== 'GET') {
        return;
    }

    const url = new URL(request.url);
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
        return;
    }

    const isBoardAsset =
        url.pathname.startsWith('/board/') ||
        url.pathname.startsWith('/static/') ||
        url.pathname.startsWith('/media/');

    if (!isBoardAsset) {
        return;
    }

    event.respondWith(networkFirstWithCacheFallback(request));
});

async function networkFirstWithCacheFallback(request) {
    let networkResponse;
    try {
        // Navigate requests use redirect: 'manual' by default, which gives an opaque
        // redirect response that Chrome can't follow cleanly. Use redirect: 'follow'
        // so we get the final response with a real URL.
        const fetchRequest = request.mode === 'navigate'
            ? new Request(request, { redirect: 'follow' })
            : request;
        networkResponse = await fetch(fetchRequest);
    } catch (error) {
        // Network failure — fall back to cache if available.
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        // Nothing cached; for board navigations show a retry page.
        const url = new URL(request.url);
        if (request.mode === 'navigate' && url.pathname.startsWith('/board/')) {
            return unavailableBoardPageResponse();
        }
        return new Response('Board unavailable.', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
        });
    }

    // If the server redirected (e.g. to the login page), pass it through.
    if (networkResponse.redirected) {
        return Response.redirect(networkResponse.url);
    }

    if (!networkResponse.ok) {
        // Server error — fall back to cache to keep the board running.
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        return networkResponse;
    }

    // Cache the response. For HTML, inject a marker so board.js can detect
    // that a later load was served from cache.
    const cache = await caches.open(CACHE_NAME);
    const contentType = networkResponse.headers.get('content-type') || '';
    if (contentType.includes('text/html')) {
        const clone = networkResponse.clone();
        const text = await clone.text();
        const markedHtml = text.replace('</head>', '<script>window.__SW_CACHED__=1;<\/script></head>');
        const headers = new Headers(clone.headers);
        headers.delete('content-length');
        headers.delete('content-encoding');
        cache.put(request, new Response(markedHtml, {
            status: clone.status,
            statusText: clone.statusText,
            headers: headers,
        }));
    } else {
        cache.put(request, networkResponse.clone());
    }

    return networkResponse;
}

function unavailableBoardPageResponse() {
    return new Response(
        `<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Offline - Missionaries</title>
            <style>
                body { background: #3a3f44; color: #aaa; font-family: sans-serif;
                       display: flex; align-items: center; justify-content: center;
                       height: 100vh; margin: 0; text-align: center; }
            </style>
        </head>
        <body>
            <p>&#x1F4E1; Board unavailable. Retrying&hellip;</p>
            <script>setTimeout(() => location.reload(), 10000);<\/script>
        </body>
        </html>`,
        {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'text/html; charset=utf-8' },
        }
    );
}
