
const CACHE_NAME = "ev-chargefinder-shell-v1";

const APP_SHELL = [
  "/",
  "/static/manifest.webmanifest",
  "/static/icons/ev-icon.svg"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);

  // Only handle this app's own origin.
  if (url.origin !== self.location.origin) return;

  // Never cache station searches or other API responses.
  if (url.pathname.startsWith("/api/")) return;

  // Cache-first for the manifest and icon.
  if (
    url.pathname === "/static/manifest.webmanifest" ||
    url.pathname === "/static/icons/ev-icon.svg"
  ) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;

        return fetch(request).then(response => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
          }
          return response;
        });
      })
    );
    return;
  }

  // Network-first for HTML pages.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then(response => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put("/", copy));
          }
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;

          const home = await caches.match("/");
          if (home) return home;

          return new Response(
            "<!doctype html><html><meta name='viewport' content='width=device-width'><title>Offline</title><body style='font-family:Arial;background:#0a1020;color:white;padding:30px'><h2>EV ChargeFinder</h2><p>You are offline. Reconnect to use route planning and station search.</p></body></html>",
            { headers: { "Content-Type": "text/html; charset=utf-8" } }
          );
        })
    );
  }
});
