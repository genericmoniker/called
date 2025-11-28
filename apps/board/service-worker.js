// Service Worker for offline board functionality
// Version: 1.0.0

const CACHE_VERSION = 'board-v1';
const CACHE_NAME = `${CACHE_VERSION}-cache`;

// Core assets to cache immediately on install
const CORE_ASSETS = [
    '/board/',
    '/static/board/static/board.css',
    '/static/img/elder.jpg',
    '/static/img/sister.jpg',
    '/static/img/couple.jpg',
    '/static/img/empty.jpg',
];

// Install event - pre-cache core assets
self.addEventListener('install', event => {
    console.log('[ServiceWorker] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[ServiceWorker] Pre-caching core assets');
                return cache.addAll(CORE_ASSETS);
            })
            .then(() => {
                console.log('[ServiceWorker] Skip waiting');
                return self.skipWaiting();
            })
            .catch(err => {
                console.error('[ServiceWorker] Pre-cache failed:', err);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('[ServiceWorker] Activating...');
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(cacheName => {
                            return cacheName.startsWith('board-') && cacheName !== CACHE_NAME;
                        })
                        .map(cacheName => {
                            console.log('[ServiceWorker] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            })
            .then(() => {
                console.log('[ServiceWorker] Claiming clients');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip chrome-extension and other non-http(s) requests
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // Handle different types of requests
    if (url.pathname.startsWith('/board/') || url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
        // All board-related requests: Network first, fallback to cache
        event.respondWith(networkFirstStrategy(request));
    }
    // Everything else: let browser handle normally
});

// Network first strategy - for all board resources
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);

        // Only cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('[ServiceWorker] Network failed, serving from cache:', request.url);
        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            // Notify clients that we're serving from cache (offline mode)
            self.clients.matchAll().then(clients => {
                clients.forEach(client => {
                    client.postMessage({ type: 'SERVING_FROM_CACHE', url: request.url });
                });
            });
            return cachedResponse;
        }

        // If no cache and network fails, return offline page
        return new Response(
            `<!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Offline - Missionaries</title>
                <style>
                    body {
                        background-color: #1a1a1a;
                        color: #ffffff;
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
                    <h1>📡 Offline</h1>
                    <p>Unable to load the board. Please check your internet connection.</p>
                    <p>The page will automatically reload when connection is restored.</p>
                </div>
                <script>
                    // Periodically check for network connectivity
                    function checkConnection() {
                        fetch('/board/', { method: 'HEAD', cache: 'no-store' })
                            .then(() => {
                                // Connection restored, reload the page
                                window.location.reload();
                            })
                            .catch(() => {
                                // Still offline, check again in 5 seconds
                                setTimeout(checkConnection, 5000);
                            });
                    }

                    // Also listen for online event
                    window.addEventListener('online', () => {
                        window.location.reload();
                    });

                    // Start checking
                    setTimeout(checkConnection, 5000);
                </script>
            </body>
            </html>`,
            { headers: { 'Content-Type': 'text/html' } }
        );
    }
}

// Listen for messages from the page
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CACHE_URLS') {
        // Cache additional URLs provided by the page
        const urls = event.data.urls;
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urls))
            .catch(err => console.error('[ServiceWorker] Failed to cache URLs:', err));
    }
});
