// Simple service worker
const CACHE_NAME = 'dastawez-v1';

self.addEventListener('install', (event) => {
  console.log('Service Worker: Installed');
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request).catch(() => {
      console.log('Offline: Serving from cache');
    })
  );
});