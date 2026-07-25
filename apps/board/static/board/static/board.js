(function () {
    var body = document.getElementById('body');
    var nextUrl = body ? body.dataset.nextUrl : '';
    var cacheIndicator = document.getElementById('cache-indicator');

    // Show the indicator if this page was served from the SW cache.
    // The cached HTML has a marker script injected at cache-time that sets this global.
    if (cacheIndicator) {
        cacheIndicator.style.display = window.__SW_CACHED__ ? 'flex' : 'none';
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
            navigator.serviceWorker.register('/board/service-worker.js', { scope: '/board/', updateViaCache: 'none' })
                .then(function (reg) {
                    console.log('[Board] ServiceWorker registered:', reg.scope);
                })
                .catch(function (err) {
                    console.log('[Board] ServiceWorker registration failed:', err);
                });
        });
    }
})();
