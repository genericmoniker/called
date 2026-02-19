// Service Worker for offline support.

// Update the version part of the CACHE_NAME string to force clients to update
// their cache when changes are made.
const CACHE_NAME = 'board-v7';

const CORE_ASSETS = [
    '/board/',
    '/static/board/static/board.css',
    '/static/board/static/board.js',
    '/static/board/static/cursor.js',
    '/static/img/elder.png',
    '/static/img/sister.png',
    '/static/img/couple.png',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(CORE_ASSETS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
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
    try {
        const networkResponse = await fetch(request);
        if (!networkResponse.ok) {
            throw new Error(`HTTP ${networkResponse.status}`);
        }
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, networkResponse.clone());
        return networkResponse;
    } catch (error) {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            notifyClientsOfflineFallback(request.url);
            return cachedResponse;
        }

        const url = new URL(request.url);
        const isBoardNavigation = request.mode === 'navigate' && url.pathname.startsWith('/board/');
        if (isBoardNavigation) {
            return unavailableBoardPageResponse(error);
        }

        return new Response('Board unavailable.', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
        });
    }
}

function unavailableBoardPageResponse(error) {
    const reason = escapeHtml(normalizeErrorReason(error));
    const retry_interval = 10000; // milliseconds

    return new Response(
        `<!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Offline / Server Busy - Missionaries</title>
                <style>
                    body {
                        background-color: #3a3f44;
                        color: #aaa;
                        font-family: sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .message {
                        text-align: center;
                        padding: 2rem;
                    }
                    h1 {
                        margin-bottom: 1rem;
                    }
                </style>
            </head>
            <body>
                <div class="message">
                    <h1>📡 Offline / Error</h1>
                    <p>Sorry, the missionary board is unavailable right now.</p>
                    <p>Reason: ${reason}</p>
                    <p>I'll keep trying...</p>
                </div>
                <script>
                    // Periodically reload and let the service worker attempt recovery.
                    function retry() {
                        window.location.reload();
                    }

                    // Start checking
                    setTimeout(retry, ${retry_interval});
                </script>
            </body>
            </html>`,
        {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'text/html; charset=utf-8' },
        }
    );
}

function normalizeErrorReason(error) {
    if (!error) {
        return 'Unknown error';
    }

    if (typeof error === 'string') {
        return error;
    }

    if (error instanceof Error && error.message) {
        return error.message;
    }

    return String(error);
}

function escapeHtml(value) {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function notifyClientsOfflineFallback(url) {
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clients) => {
            clients.forEach((client) => {
                client.postMessage({ type: 'BOARD_OFFLINE_FALLBACK', url: url });
            });
        });
}
