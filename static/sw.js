// TutorPro PWA Service Worker
const CACHE_VERSION = 'v1';
const CACHE_NAME = 'tutorpro-pwa';

// Static assets that should be cached
const STATIC_ASSETS = [
  '/',
  '/static/css/bootstrap.min.css',
  '/static/css/responsive.css',
  '/static/js/jquery.min.js',
  '/static/js/bootstrap.min.js',
  '/static/images/logo.png'
];

// Dynamic routes that should be network-first
const DYNAMIC_ROUTES = [
  '/dashboard',
  '/profile',
  '/courses',
  '/messages',
  '/schedule',
  '/bookings',
  '/notifications'
];

// Install event
self.addEventListener('install', event => {
  console.log('PWA installed');
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', event => {
  console.log('PWA activated');
  
  // Clean up old caches
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
});

// Fetch event - Network-first strategy with offline fallback
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Check if request is for a static asset
  const isStaticAsset = STATIC_ASSETS.some(asset => request.url.includes(asset));
  
  // Check if request is for a dynamic route
  const isDynamicRoute = DYNAMIC_ROUTES.some(route => request.url.includes(route));
  
  if (isStaticAsset) {
    // Serve from cache with network fallback
    event.respondWith(
      caches.match(request)
        .then(response => {
          if (response) {
            return response;
          }
          
          // If not in cache, fetch from network
          return fetch(request)
            .then(response => {
              // Cache successful responses
              if (response.ok && DYNAMIC_ROUTES.some(route => request.url.includes(route))) {
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                  cache.put(request, responseClone);
                });
              }
              return response;
            })
            .catch(() => {
              // Offline fallback for static assets
              return new Response('Offline - Content not available', {
                status: 503,
                statusText: 'Service Unavailable'
              });
            });
        })
    );
  } else if (isDynamicRoute) {
    // Network-first for dynamic routes (always fresh data)
    event.respondWith(
      fetch(request)
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
          // Offline fallback for dynamic routes
          return caches.match(request).then(response => {
            return response || new Response('Offline - Connection required', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
        })
    );
  } else {
    // For other requests, try cache first, then network
    event.respondWith(
      caches.match(request)
        .then(response => {
          if (response) {
            return response;
          }
          
          // Otherwise fetch from network
          return fetch(request);
        })
        .catch(() => {
          return fetch(request);
        })
    );
  }
});

// Background sync for offline data
self.addEventListener('sync', event => {
  console.log('Background sync triggered');
  
  if (event.tag === 'sync-messages') {
    // Sync offline messages when back online
    syncOfflineMessages();
  } else if (event.tag === 'sync-bookings') {
    // Sync offline booking changes
    syncOfflineBookings();
  }
});

// Sync offline messages
function syncOfflineMessages() {
  // Get messages stored in IndexedDB
  getOfflineMessages().then(messages => {
    if (messages.length > 0) {
      // Send to server
      fetch('/api/sync/offline-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: 'messages',
          data: messages
        })
      })
      .then(response => {
        if (response.ok) {
          // Clear synced messages
          clearOfflineMessages();
        }
      })
      .catch(error => {
        console.error('Sync failed:', error);
      });
    }
  });
}

// Sync offline bookings
function syncOfflineBookings() {
  // Get booking changes stored in IndexedDB
  getOfflineBookings().then(bookings => {
    if (bookings.length > 0) {
      // Send to server
      fetch('/api/sync/offline-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: 'bookings',
          data: bookings
        })
      })
      .then(response => {
        if (response.ok) {
          // Clear synced bookings
          clearOfflineBookings();
        }
      })
      .catch(error => {
        console.error('Sync failed:', error);
      });
    }
  });
}

// IndexedDB helpers for offline storage
function getOfflineMessages() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TutorProOffline', 1);
    request.onsuccess = event => {
      const db = event.target.result;
      const transaction = db.transaction(['messages'], 'readonly');
      const store = transaction.objectStore('messages');
      const getAllRequest = store.getAll();
      
      getAllRequest.onsuccess = event => {
        resolve(event.target.result || []);
      };
      
      getAllRequest.onerror = () => {
        reject(new Error('Failed to get offline messages'));
      };
    };
    
    request.onerror = () => {
      reject(new Error('Failed to open offline storage'));
    };
  });
}

function clearOfflineMessages() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TutorProOffline', 1);
    request.onsuccess = event => {
      const db = event.target.result;
      const transaction = db.transaction(['messages'], 'readwrite');
      const store = transaction.objectStore('messages');
      const clearRequest = store.clear();
      
      clearRequest.onsuccess = () => {
        resolve();
      };
      
      clearRequest.onerror = () => {
        reject(new Error('Failed to clear offline messages'));
      };
    };
    
    request.onerror = () => {
      reject(new Error('Failed to open offline storage'));
    };
  });
}

function getOfflineBookings() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TutorProOffline', 1);
    request.onsuccess = event => {
      const db = event.target.result;
      const transaction = db.transaction(['bookings'], 'readonly');
      const store = transaction.objectStore('bookings');
      const getAllRequest = store.getAll();
      
      getAllRequest.onsuccess = event => {
        resolve(event.target.result || []);
      };
      
      getAllRequest.onerror = () => {
        reject(new Error('Failed to get offline bookings'));
      };
    };
    
    request.onerror = () => {
      reject(new Error('Failed to open offline storage'));
    };
  });
}

function clearOfflineBookings() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TutorProOffline', 1);
    request.onsuccess = event => {
      const db = event.target.result;
      const transaction = db.transaction(['bookings'], 'readwrite');
      const store = transaction.objectStore('bookings');
      const clearRequest = store.clear();
      
      clearRequest.onsuccess = () => {
        resolve();
      };
      
      clearRequest.onerror = () => {
        reject(new Error('Failed to clear offline bookings'));
      };
    };
    
    request.onerror = () => {
      reject(new Error('Failed to open offline storage'));
    };
  });
}