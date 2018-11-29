importScripts('https://storage.googleapis.com/workbox-cdn/releases/3.6.1/workbox-sw.js');

workbox.routing.registerRoute(
    new RegExp('https://cdn.jsdelivr.net/npm'),
    workbox.strategies.networkFirst()
);

workbox.routing.registerRoute(
    new RegExp('/'),
    workbox.strategies.networkFirst()
);

workbox.routing.registerRoute(
    new RegExp('/inventory.js'),
    workbox.strategies.networkFirst()
);