(function () {
    var body = document.getElementById('body');
    var nextUrl = body ? body.dataset.nextUrl : '';
    var offlineIndicator = document.getElementById('offline-indicator');
    var servingFromCache = false;

    function setOfflineIndicator(visible) {
        if (!offlineIndicator) {
            return;
        }
        offlineIndicator.style.display = visible ? 'block' : 'none';
    }

    function refreshOfflineIndicator() {
        setOfflineIndicator(!navigator.onLine || servingFromCache);
    }

    // Fade out on navigation.
    window.onbeforeunload = function () {
        if (body) {
            body.className = 'fadeout';
        }
    };

    // Spacebar navigation.
    document.addEventListener('keydown', function (event) {
        if (event.key !== ' ' || !nextUrl) {
            return;
        }

        var target = event.target;
        if (target && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))) {
            return;
        }

        event.preventDefault();
        window.location.href = nextUrl;
    });

    // True zoom scaling for .viewport, using CSS variables for TV size.
    function scaleViewport() {
        var viewport = document.querySelector('.viewport');
        if (!viewport) {
            return;
        }

        var styles = getComputedStyle(viewport);
        var boardW = parseInt(styles.getPropertyValue('--tv-width'), 10);
        var boardH = parseInt(styles.getPropertyValue('--tv-height'), 10);
        if (!boardW || !boardH) {
            return;
        }

        var scale = Math.min(window.innerWidth / boardW, window.innerHeight / boardH);
        viewport.style.transform = 'translate(-50%, -50%) scale(' + scale + ')';
    }

    window.addEventListener('resize', scaleViewport);
    window.addEventListener('DOMContentLoaded', scaleViewport);

    // Register Service Worker for offline support.
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function () {
            navigator.serviceWorker.register('/board/service-worker.js', { scope: '/board/' })
                .then(function (registration) {
                    console.log('[Board] ServiceWorker registered:', registration.scope);
                })
                .catch(function (error) {
                    console.log('[Board] ServiceWorker registration failed:', error);
                });
        });

        navigator.serviceWorker.addEventListener('message', function (event) {
            if (event.data && event.data.type === 'BOARD_OFFLINE_FALLBACK') {
                servingFromCache = true;
                refreshOfflineIndicator();
            }
        });
    }

    window.addEventListener('online', function () {
        servingFromCache = false;
        refreshOfflineIndicator();
    });

    window.addEventListener('offline', refreshOfflineIndicator);

    // While browser reports online, probe board endpoint so we can clear fallback state
    // after transient server/network errors recover.
    setInterval(function () {
        if (!servingFromCache || !navigator.onLine) {
            return;
        }

        fetch('/board/', { method: 'HEAD', cache: 'no-store' })
            .then(function (response) {
                if (response.ok) {
                    servingFromCache = false;
                    refreshOfflineIndicator();
                }
            })
            .catch(function () {
                // Keep indicator visible while recovery probe fails.
            });
    }, 10000);

    refreshOfflineIndicator();
})();
