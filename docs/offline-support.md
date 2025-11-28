# Offline Support for Board App

*Written mostly by Claude Sonnet 4.5*

## Overview

The board app supports offline viewing through Service Worker-based caching.
After an initial online visit, the board continues to display missionary
information and auto-rotate through pages even when the internet connection is
unavailable.

## How It Works

### Service Worker Architecture

The board uses a single Service Worker (`/board/service-worker.js`) that
implements a **network-first caching strategy** for all board resources:

- **Board pages** (`/board/*`) - HTML content with missionary data
- **Static assets** (`/static/*`) - CSS files and default images
- **Media files** (`/media/*`) - Uploaded missionary photos

#### Network-First Strategy

When a request is made:

1. **Online**: Fetch from network, cache the response, return fresh content
2. **Offline**: Network fails, serve from cache, show offline indicator
3. **Not cached**: Network fails and no cache exists, show dark-themed offline
   page with auto-recovery

This ensures users always get fresh data when online while maintaining full
functionality offline.

### Cache Management

The Service Worker uses a single cache (`board-v1-cache`) for all resources:

- **Installation**: Pre-caches core assets (first board page, CSS, default
  images)
- **Runtime**: Caches additional resources as they're accessed (pagination
  pages, photos)
- **Activation**: Cleans up old cache versions when version changes
- **Updates**: Automatically installs new Service Worker versions and reloads
  the page

#### When to Change Cache Version

Update the `CACHE_VERSION` constant in `service-worker.js` when:

- **Service Worker logic changes**: New caching strategies, bug fixes, fetch
  handling changes
- **Pre-cached assets change**: Different assets in `CORE_ASSETS` array (not
  changes to those assets already listed)
- **Cache structure changes**: Switching from multiple caches to single cache,
  etc.
- **Force cache refresh**: Need to clear all users' cached content (rarely
  needed)

Incrementing the version (e.g., `'board-v1'` → `'board-v2'`) will:

1. Install the new Service Worker alongside the old one
2. Delete old cache versions on activation
3. Pre-cache new core assets
4. Automatically reload active pages to use the new version

**Note**: You typically don't need to change the version for:
- **Content updates**: New missionaries, edited photos, changed data
- **Static asset updates**: CSS changes, image updates
- **HTML changes**: Template modifications

These are all automatically updated through the network-first strategy when users
are online.

### Offline Indicator

A visual indicator shows when the board is operating offline:

- **Detection methods**:
  - `navigator.onLine` browser API (network interface status)
  - Service Worker messages when serving from cache due to network failure
  - Failed fetch requests (fallback detection)

- **Appearance**: Red badge ("📡 Offline Mode") in top-right corner
- **Behavior**: Shows immediately when offline, hides when connectivity returns

### Session Management

- **Session timeout**: 30 days (extended from default 7 days)
- **Reason**: Board often runs on dedicated displays (TV/kiosk) with expected
  offline periods
- **Limitation**: Must re-authenticate if session expires while offline
- **Auto-refresh**: `SESSION_SAVE_EVERY_REQUEST` keeps session alive during
  auto-rotation

### Offline Page

If a page isn't cached and network fails, users see a fallback offline page:

- **Dark theme**: Matches board's dark background (#1a1a1a)
- **Auto-recovery**: Checks for connectivity every 5 seconds
- **Automatic reload**: Reloads page when connection restored
- **Rare occurrence**: Most users see cached content with offline indicator
  instead

### File Serving

The Service Worker file is served via Django view (`service_worker` in
`views.py`):

- **URL**: `/board/service-worker.js`
- **Reason**: Service Workers must be served from same path or above their scope
- **Scope**: Controls all `/board/*` URLs
- **Source**: Reads from `apps/board/static/board/service-worker.js`

## Testing Instructions

### Basic Offline Test

1. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

2. **Visit the board** (while online):
   - Navigate to `http://localhost:8000/board/`
   - Log in if needed
   - Wait for page to load completely
   - Open browser DevTools (F12) → Console tab
   - Verify message: "ServiceWorker registered: /board/"

3. **Enable offline mode**:
   - In DevTools → Network tab
   - Check the "Offline" checkbox (or throttle to "Offline")
   - Or use Application tab → Service Workers → "Offline" checkbox

4. **Test offline functionality**:
   - Reload the page (Ctrl+R or Cmd+R)
   - Page should load from cache
   - Red "📡 Offline Mode" indicator appears
   - Auto-refresh should work (wait 30 seconds or press spacebar)
   - Navigate through pages - all visited pages are cached

5. **Return online**:
   - Uncheck "Offline" in DevTools
   - Reload page (or wait for auto-refresh)
   - Indicator disappears
   - Fresh data loads from server

### Advanced Testing

#### Test Cache Updates

1. While online, add a new missionary via admin
2. Reload board - new missionary appears
3. Go offline
4. Reload board - new missionary still appears (was cached during step 2)

#### Test Photo Caching

1. Visit board pages while online (photos are cached as you view them)
2. Go offline
3. Navigate through pages
4. Previously viewed photos display normally
5. New pages you haven't visited show default images (elder/sister/couple)

#### Test Service Worker Updates

1. Edit `apps/board/static/board/service-worker.js`
2. Change `CACHE_VERSION` from `'board-v1'` to `'board-v2'`
3. Reload page
4. Check console for "New ServiceWorker available"
5. Page automatically reloads with new service worker
6. Old cache is deleted, new cache is created

#### Test Session Expiry

1. Clear cookies (DevTools → Application → Cookies → Delete all)
2. Go offline
3. Reload page
4. Redirected to login (can't authenticate offline)

#### Test Offline Recovery Page

1. Clear Service Worker cache (DevTools → Application → Cache Storage → Delete
   all)
2. Unregister Service Worker (DevTools → Application → Service Workers →
   Unregister)
3. Go offline
4. Navigate to `/board/`
5. See dark-themed offline page
6. Return online (uncheck "Offline" in DevTools)
7. Page automatically reloads within 5 seconds

## Browser DevTools Inspection

### View Cached Assets

1. Open DevTools → Application tab
2. Navigate to "Cache Storage"
3. Expand to see `board-v1-cache` containing:
   - Board HTML pages (`/board/?offset=0`, etc.)
   - CSS files (`/static/board/static/board.css`)
   - Default images (`/static/img/elder.jpg`, etc.)
   - Missionary photos (`/media/missionaries/photos/*`)

### View Service Worker Status

1. DevTools → Application → Service Workers
2. See registration status, scope (`/board/`), and version
3. Use "Update" to force check for new version
4. Use "Unregister" to remove (for testing clean installs)
5. Click "Offline" checkbox to simulate offline mode

### Monitor Network Requests

1. DevTools → Network tab
2. Online requests show normal status codes (200, 304, etc.)
3. Offline requests served from Service Worker show "(from ServiceWorker)" in
   Size column
4. Check "Disable cache" to bypass HTTP cache but still use Service Worker

## Limitations

1. **Authentication Required**: Must log in online first; session must be valid
   to access cached content
2. **Cache Storage Limits**: Browser quotas (typically 50MB+, varies by browser
   and available storage)
3. **Stale Data**: Offline mode shows last-cached data, not live updates
4. **Write Operations**: Preview save (photo editing) doesn't work offline
5. **Initial Load**: First visit must be online to install Service Worker and
   cache resources
6. **Uncached Pages**: Pages not yet visited won't be available offline

## Architecture Decisions

### Why Network-First for Everything?

- **Simplicity**: Single strategy for all resources, easier to understand and
  maintain
- **Freshness**: Always get latest content when online
- **Graceful degradation**: Automatically falls back to cache when offline
- **Auto-updates**: Content updates without manual cache invalidation

### Why Single Cache?

- **Simplicity**: One cache to manage, fewer moving parts
- **Efficiency**: No duplicate caching logic, single version cleanup
- **Sufficient**: Network-first strategy handles both static and dynamic content
  appropriately

### Why 30-Day Session?

- Board is often on dedicated display (TV/kiosk) with minimal user interaction
- Longer offline periods expected (network outages, maintenance)
- Still requires re-authentication monthly for security
- Balance between usability and security

### Why Serve Service Worker via Django?

- Service Workers can only control paths at or below their location
- Serving from `/static/` would limit scope to `/static/*`
- Django view at `/board/service-worker.js` allows `/board/*` scope
- Simple file read from static location, no additional complexity

## Files

1. **`apps/board/static/board/service-worker.js`** - Service Worker
   implementation
2. **`apps/board/templates/board/base.html`** - Service Worker registration and
   offline indicator
3. **`apps/board/views.py`** - `service_worker` view to serve JS file
4. **`apps/board/urls.py`** - `/service-worker.js` route
5. **`called/settings.py`** - Extended `SESSION_COOKIE_AGE` to 30 days
6. **`static/favicon.ico`** - Minimal favicon to prevent 404s

## Troubleshooting

### Service Worker Not Registering

- Check browser console for errors
- Ensure HTTPS (or localhost for development)
- Verify `/board/service-worker.js` returns JavaScript content
- Check that `service_worker` view exists and file path is correct

### Pages Not Loading Offline

- Verify pages were visited while online (to cache them)
- Inspect Cache Storage in DevTools to confirm cached content
- Check Service Worker is active (not just installing/waiting)
- Ensure session hasn't expired (check cookies)

### Offline Indicator Not Showing

- Service Worker must be serving from cache (check console for "Network failed"
  messages)
- Check browser console for Service Worker message events
- Test with actual network disconnect (not just DevTools) to verify
  `navigator.onLine`
- Verify indicator element exists in DOM

### Old Content Showing After Updates

- Increment `CACHE_VERSION` in `service-worker.js`
- Hard refresh page (Ctrl+Shift+R / Cmd+Shift+R)
- Or clear caches manually: DevTools → Application → Clear storage
- Check that old cache version was deleted during activation

### Service Worker Not Updating

- Browser caches Service Worker file for 24 hours by default
- Use "Update" button in DevTools → Application → Service Workers
- Or add `?v=2` query parameter when testing (e.g., change registration URL
  temporarily)
- In production, increment `CACHE_VERSION` which triggers full update cycle
