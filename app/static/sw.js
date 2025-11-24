// TutorPro Service Worker
const CACHE_NAME = 'tutorpro-v1.0.0';
const OFFLINE_URL = '/offline';

// Assets to cache for offline functionality
const STATIC_CACHE_URLS = [
  '/',
  '/dashboard',
  '/tutors',
  '/courses',
  '/static/css/responsive.css',
  '/static/js/drag-drop-reschedule.js',
  '/static/js/conflict-detection.js',
  '/static/js/automated-reminders.js',
  '/static/js/timezone-support.js',
  '/static/js/recurring-bookings.js',
  '/static/js/ui-enhancements.js',
  '/static/js/pwa-install.js',
  '/static/images/logo.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://code.jquery.com/jquery-3.6.0.min.js'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .then(() => {
        console.log('Service Worker: Installation complete');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker: Installation failed', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activation complete');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip external requests (except for CDNs we trust)
  if (url.origin !== location.origin && 
      !url.hostname.includes('cdn.jsdelivr.net') && 
      !url.hostname.includes('cdnjs.cloudflare.com') &&
      !url.hostname.includes('code.jquery.com')) {
    return;
  }
  
  event.respondWith(
    caches.match(request)
      .then(response => {
        // Return cached version if available
        if (response) {
          // For API requests, try network first but serve cache if network fails
          if (url.pathname.startsWith('/api/')) {
            return fetch(request)
              .then(networkResponse => {
                // Cache successful API responses
                if (networkResponse.ok) {
                  const responseClone = networkResponse.clone();
                  caches.open(CACHE_NAME).then(cache => {
                    cache.put(request, responseClone);
                  });
                }
                return networkResponse;
              })
              .catch(() => {
                // Network failed, return cached version
                return response;
              });
          }
          return response;
        }
        
        // For navigation requests, try network first
        if (request.mode === 'navigate') {
          return fetch(request)
            .then(response => {
              // Cache successful navigation responses
              if (response.ok) {
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                  cache.put(request, responseClone);
                });
              }
              return response;
            })
            .catch(() => {
              // Network failed, try to serve offline page
              return caches.match(OFFLINE_URL);
            });
        }
        
        // For other requests, try network with cache fallback
        return fetch(request)
          .then(response => {
            // Cache successful responses
            if (response.ok) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME).then(cache => {
                cache.put(request, responseClone);
              });
            }
            return response;
          })
          .catch(() => {
            // Network failed, return appropriate error
            if (request.destination === 'image') {
              return new Response(
                '<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#ccc"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#666">No Image</text></svg>',
                { headers: { 'Content-Type': 'image/svg+xml' } }
              );
            }
            return new Response('Offline - No network connection', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', event => {
  console.log('Service Worker: Background sync', event.tag);
  
  if (event.tag === 'background-sync-bookings') {
    event.waitUntil(syncBookings());
  } else if (event.tag === 'background-sync-messages') {
    event.waitUntil(syncMessages());
  }
});

// Push notification handling
self.addEventListener('push', event => {
  console.log('Service Worker: Push notification received');
  
  const options = {
    body: event.data ? event.data.text() : 'New notification from TutorPro',
    icon: '/static/images/icons/icon-192x192.png',
    badge: '/static/images/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Explore',
        icon: '/static/images/icons/action-explore.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/images/icons/action-close.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('TutorPro', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  console.log('Service Worker: Notification click received');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Sync bookings when back online
async function syncBookings() {
  try {
    const cachedBookings = await caches.match('/api/sync/bookings');
    if (cachedBookings) {
      const bookings = await cachedBookings.json();
      
      for (const booking of bookings) {
        await fetch('/api/bookings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(booking)
        });
      }
      
      // Clear synced bookings from cache
      await caches.delete('/api/sync/bookings');
    }
  } catch (error) {
    console.error('Service Worker: Failed to sync bookings', error);
  }
}

// Sync messages when back online
async function syncMessages() {
  try {
    const cachedMessages = await caches.match('/api/sync/messages');
    if (cachedMessages) {
      const messages = await cachedMessages.json();
      
      for (const message of messages) {
        await fetch('/api/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(message)
        });
      }
      
      // Clear synced messages from cache
      await caches.delete('/api/sync/messages');
    }
  } catch (error) {
    console.error('Service Worker: Failed to sync messages', error);
  }
}

// Periodic background sync for content updates
self.addEventListener('periodicsync', event => {
  console.log('Service Worker: Periodic sync', event.tag);
  
  if (event.tag === 'content-update') {
    event.waitUntil(updateContent());
  }
});

// Update cached content periodically
async function updateContent() {
  try {
    const cache = await caches.open(CACHE_NAME);
    
    // Update key pages
    const pagesToUpdate = ['/', '/tutors', '/courses'];
    
    for (const page of pagesToUpdate) {
      try {
        const response = await fetch(page);
        if (response.ok) {
          await cache.put(page, response);
        }
      } catch (error) {
        console.log(`Service Worker: Failed to update ${page}`, error);
      }
    }
  } catch (error) {
    console.error('Service Worker: Failed to update content', error);
  }
}

// Handle messages from the main app
self.addEventListener('message', event => {
  console.log('Service Worker: Message received', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_UPDATE') {
    updateContent();
  }
});

// Cleanup on unload
self.addEventListener('beforeunload', event => {
  console.log('Service Worker: Unloading...');
});