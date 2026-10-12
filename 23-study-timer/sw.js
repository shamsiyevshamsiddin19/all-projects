/**
 * Zenith Study Timer — service worker.
 *
 * Strategiya:
 *   - ilova qobig'i (app shell) o'rnatishda keshlanadi → oflayn ishlaydi;
 *   - shriftlar (Google Fonts CSS va woff2) birinchi yuklanishda keshga olinadi,
 *     shundan keyin internetsiz ham tipografiya saqlanadi;
 *   - navigatsiya: avval tarmoq, uzilsa keshdagi index.html;
 *   - /api/data hech qachon keshlanmaydi.
 */
const VERSION = 'zenith-v2';
const SHELL_CACHE = `${VERSION}-shell`;
const FONT_CACHE = `${VERSION}-fonts`;

const SHELL_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './css/style.css',
  './js/app.js',
  './js/ui.js',
  './js/storage.js',
  './js/audio.js',
  './js/platform.js',
  './js/i18n.js',
  './js/format.js',
  './js/constants.js',
  './js/engine/countdown.js',
  './js/engine/timer-engine.js',
  './icons/icon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

const FONT_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then((cache) => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => !key.startsWith(VERSION)).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Ma'lumot API'si hech qachon keshlanmaydi
  if (url.pathname.endsWith('/api/data')) return;

  // Shriftlar: avval kesh, keyin tarmoq (oflayn tipografiya)
  if (FONT_HOSTS.includes(url.hostname)) {
    event.respondWith(cacheFirst(request, FONT_CACHE));
    return;
  }

  if (url.origin !== self.location.origin) return;

  // Navigatsiya: avval tarmoq, uzilsa keshdagi qobiq
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(SHELL_CACHE).then((cache) => cache.put('./index.html', copy));
          return response;
        })
        .catch(() => caches.match('./index.html'))
    );
    return;
  }

  event.respondWith(cacheFirst(request, SHELL_CACHE));
});

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response && (response.ok || response.type === 'opaque')) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const fallback = await caches.match('./index.html');
    if (fallback) return fallback;
    throw err;
  }
}
