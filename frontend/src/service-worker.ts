/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />
/// <reference types="@sveltejs/kit" />

import { build, files, version } from "$service-worker"

const self = globalThis.self as unknown as ServiceWorkerGlobalScope

const KEY = `cache-${version}`

const CACHE = [...build, ...files]

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(KEY).then((cache) => cache.addAll(CACHE)))
})

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map(async (key) => {
          if (key !== KEY) return caches.delete(key)
        }),
      ),
    ),
  )
})

self.addEventListener("push", (event) => {
  if (!event.data) return
  const { displayName, username, url, game, title } = event.data.json()
  event.waitUntil(
    self.registration.showNotification(
      `${displayName || `@${username}`} started streaming ${game}: ${title}`,
      { body: "Join now to watch live on Inter.", data: { url } },
    ),
  )
})

self.addEventListener("pushsubscriptionchange", (event) => {
  event.waitUntil(
    self.registration.pushManager
      .subscribe(event.oldSubscription?.options)
      .then(async (subscription) => {
        const [p256dh, auth] = [subscription.getKey("p256dh"), subscription.getKey("auth")]
        if (!p256dh || !auth) return
        const form = new FormData()
        form.append("endpoint", subscription.endpoint)
        form.append("p256dh", new Blob([p256dh]))
        form.append("auth", new Blob([auth]))
        return this.post(`/${encodeURIComponent(username)}/notify`, form)
      }),
  )
})

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return

  event.respondWith(
    (async () => {
      const pathname = new URL(event.request.url).pathname
      const cache = await caches.open(KEY)
      if (CACHE.includes(pathname)) {
        const response = await cache.match(pathname)
        if (response) return response
      }
      try {
        const response = await fetch(event.request)
        if (!(response instanceof Response)) {
          throw new Error("offline")
        }
        if (response.status === 200) {
          cache.put(event.request, response.clone())
        }
        return response
      } catch {
        const response = await cache.match(event.request)
        if (response) return response
      }
    })(),
  )
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()
  const { url } = event.notification.data
  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clients: readonly WindowClient[]) => {
        clients.forEach((client) => {
          if (client.url === url && "focus" in client) return client.focus()
        })
        if (self.clients.openWindow) return self.clients.openWindow(url)
      }),
  )
})
