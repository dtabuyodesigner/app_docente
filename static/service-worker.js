// Service Worker — Cuaderno del Tutor
// Estrategia: Cache-first para la shell estática, network-first para las APIs

const CACHE_NAME = 'cuaderno-tutor-v3';

// Archivos de la "shell" que se cachean al instalar
const SHELL_ASSETS = [
    '/',
    '/alumnos',
    '/asistencia',
    '/evaluacion',
    '/biblioteca',
    '/programacion',
    '/static/js/api.js',
];

// ── INSTALL: pre-cachear la shell ─────────────────────────────────────────────
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL_ASSETS))
    );
    self.skipWaiting();
});

// ── ACTIVATE: limpiar cachés antiguas ─────────────────────────────────────────
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// ── FETCH: network-first para /api/, cache-first para el resto ────────────────
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Las peticiones a la API siempre van a la red
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(fetch(event.request));
        return;
    }

    // Para el resto: intenta red primero, si falla devuelve caché
    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Guardar una copia fresca en caché
                if (response.ok && event.request.method === 'GET') {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});
