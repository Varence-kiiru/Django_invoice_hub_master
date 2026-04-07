/**
 * Service Worker for Invoicing App
 * Provides offline support, caching, and PWA features
 */

const CACHE_NAME = 'invoicing-app-v2.0.1';
const URLS_TO_CACHE = [
  '/',
  '/dashboard/',
  '/auth/login/',
  '/offline.html'
];

/**
 * Install event - cache essential files
 */
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(URLS_TO_CACHE).catch(err => {
          console.log('Cache addAll error:', err);
          // Don't fail installation if some files are missing
          return Promise.resolve();
        });
      })
  );
  self.skipWaiting();
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

/**
 * Fetch event - serve from cache, fallback to network
 */
self.addEventListener('fetch', event => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip certain URLs
  if (event.request.url.includes('/admin/') ||
      event.request.url.includes('/api/') ||
      event.request.url.includes('chrome-extension://')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version if available
        if (response) {
          return response;
        }

        // Try to fetch from network
        return fetch(event.request)
          .then(response => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type === 'error') {
              return response;
            }

            // Clone the response
            const responseToCache = response.clone();

            // Cache successful GET requests
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return response;
          })
          .catch(() => {
            // Network failed, try to return offline page
            return caches.match('/offline.html');
          });
      })
  );
});

/**
 * Handle background sync for offline form submissions
 */
self.addEventListener('sync', event => {
  if (event.tag === 'sync-invoices') {
    event.waitUntil(syncInvoices());
  }
});

async function syncInvoices() {
  try {
    // Attempt to sync any pending invoices
    const response = await fetch('/api/sync/');
    return response.json();
  } catch (error) {
    console.log('Sync failed:', error);
  }
}

/**
 * Handle push notifications
 */
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const options = {
    body: data.body || 'New notification',
    icon: '/static/images/logo.png',
    badge: '/static/images/badge.png',
    tag: data.tag || 'notification'
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'Invoicing App', options)
  );
});

/**
 * Handle notification clicks
 */
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(clientList => {
      // Check if app is already open
      for (let i = 0; i < clientList.length; i++) {
        if (clientList[i].url === '/' && 'focus' in clientList[i]) {
          return clientList[i].focus();
        }
      }
      // Open app if not already open
      if (clients.openWindow) {
        return clients.openWindow(event.notification.data.url || '/');
      }
    })
  );
});
