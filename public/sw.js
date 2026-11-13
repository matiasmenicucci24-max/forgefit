// ForgeFit — service worker
// Estrategia deliberadamente conservadora: SOLO cachea archivos estáticos
// (CSS, JS, íconos, manifest) para que la app cargue más rápido e instalada.
// Nunca intercepta pedidos a /api/ ni a las páginas HTML, para no arriesgar
// mostrar contenido viejo, romper el login, o interferir con envíos de datos.

const CACHE_NAME = "forgefit-static-v4";
const ARCHIVOS_CORE = [
  "/static/style.css",
  "/static/script.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ARCHIVOS_CORE)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((nombres) =>
      Promise.all(
        nombres
          .filter((nombre) => nombre !== CACHE_NAME)
          .map((nombre) => caches.delete(nombre))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Solo intervenimos en pedidos GET a archivos estáticos propios.
  // Todo lo demás (páginas, /api/, POST, DELETE, etc.) pasa directo a la red
  // sin que el service worker lo toque.
  const esEstaticoPropio = event.request.method === "GET" && url.origin === self.location.origin && url.pathname.startsWith("/static/");
  if (!esEstaticoPropio) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((respuestaCache) => {
      const fetchPromesa = fetch(event.request)
        .then((respuestaRed) => {
          if (respuestaRed && respuestaRed.status === 200) {
            const copia = respuestaRed.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copia)).catch(() => {});
          }
          return respuestaRed;
        })
        .catch(() => respuestaCache); // sin internet: usamos lo cacheado si existe

      // Cache-first para velocidad; si no hay nada cacheado, esperamos la red.
      return respuestaCache || fetchPromesa;
    })
  );
});
