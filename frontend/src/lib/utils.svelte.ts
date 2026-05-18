import type { Fragment } from "../models/message"
import type { User } from "../models/user"
import tailwindColours from "tailwindcss/colors"
import { toast } from "svelte-sonner"
import { onMount } from "svelte"
import { DateTime } from "luxon"
import wildcardMatch from "wildcard-match"
import { SvelteDate } from "svelte/reactivity"

function debounce<A extends unknown[]>(f: (...args: A) => unknown, ms: number) {
  let timeout: number | null = null
  return (...args: A) => {
    if (timeout !== null) {
      window.clearTimeout(timeout)
    }
    timeout = window.setTimeout(() => f(...args), ms)
  }
}

export function debounced<T>(get: () => T, ms: number) {
  let state = $state(get())
  const update = debounce((value) => {
    state = value
  }, ms)
  $effect(() => update(get()))
  return () => state
}

export const validateUsername = async (username: string) => {
  if (!/^[a-z0-9_]*$/.test(username)) {
    return "Choose a username with only lowercase letters, numbers, and underscores."
  }
  if (username.length < 4) {
    return "Choose a username with at least 4 characters."
  }
  if (username.length > 32) {
    return "Choose a username with at most 32 characters."
  }
  if (!(await server.auth.available(username))) {
    return "Username is already taken."
  }
  return null
}

export const apiBase = "/api/v1"

export function serverWithFetch(f: typeof window.fetch) {
  function createBase(f: typeof window.fetch, path: string) {
    return {
      async _fetch(url, init) {
        return f(this.resolve(url), { ...init, credentials: "same-origin" })
      },
      resolve(url: string) {
        return path + url
      },
      get(url: URL, headers?: HeadersInit) {
        return this._fetch(url, { method: "GET", headers })
      },
      post(url: URL, body?: BodyInit, headers?: HeadersInit) {
        return this._fetch(url, { method: "POST", body, headers })
      },
      postJSON(url: URL, data: unknown) {
        return this.post(url, JSON.stringify(data), { "Content-Type": "application/json" })
      },
    }
  }
  return {
    ...createBase(f, apiBase),
    async random() {
      return (await this.get("/random")).text()
    },
    async search(query: string): Promise<{ name: string; results: string[] }[]> {
      return (await this.get(`/search/${encodeURIComponent(query)}`)).json()
    },
    async emotes(): Promise<{ [key: string]: [string, boolean] }> {
      return (await this.get("/emotes")).json()
    },
    user: {
      ...createBase(f, `${apiBase}/user`),
      avatar(username: string) {
        return this.resolve(`/${encodeURIComponent(username)}/avatar`)
      },
      async user(
        username: string,
      ): Promise<{ displayName: string; colour: number; following: number; followers: number }> {
        return (await this.get(`/${encodeURIComponent(username)}`)).json()
      },
      async follow(username: string) {
        return this.post(`/${encodeURIComponent(username)}/follow`)
      },
      async unfollow(username: string) {
        return this.post(`/${encodeURIComponent(username)}/unfollow`)
      },
      async followers(username: string): Promise<number> {
        return (await this.get(`/${encodeURIComponent(username)}/followers`)).json()
      },
      async following(username: string): Promise<number> {
        return (await this.get(`/${encodeURIComponent(username)}/following`)).json()
      },
      async getNotify(username: string): Promise<"all" | "none"> {
        return (await this.get(`/${encodeURIComponent(username)}/notify`)).text()
      },
      async setNotify(
        username: string,
        subscription: { endpoint: string; keys: { p256dh: ArrayBuffer; auth: ArrayBuffer } } | null,
      ) {
        const form = new FormData()
        if (subscription !== null) {
          form.append("endpoint", subscription.endpoint)
          form.append("p256dh", new Blob([subscription.keys.p256dh]))
          form.append("auth", new Blob([subscription.keys.auth]))
        }
        return this.post(`/${encodeURIComponent(username)}/notify`, form)
      },
      async stream(
        username: string,
      ): Promise<{ title: string; game: string; start: number | null; viewers: number | null }> {
        return (await this.get(`/${encodeURIComponent(username)}/stream`)).json()
      },
      streamPreview(username: string) {
        return this.resolve(`/${encodeURIComponent(username)}/stream/preview`)
      },
      async moderate(username: string, subject: string, duration: number | null | undefined) {
        return this.postJSON(
          `/${encodeURIComponent(username)}/moderate/${encodeURIComponent(subject)}`,
          { duration },
        ).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            toast.error("Error while moderating user", { description: text })
            return Promise.reject(text)
          }
          if (duration === undefined) toast.success("Pardoned user successfully")
          else if (duration === null) toast.success("Banned user successfully")
          else toast.success(`Banned user for ${duration} seconds`)
        })
      },
      async getRoles(username: string, subject: string): Promise<number[]> {
        return (
          await this.get(`/${encodeURIComponent(username)}/roles/${encodeURIComponent(subject)}`)
        ).json()
      },
      async setRoles(username: string, subject: string, roles: number[]) {
        return this.postJSON(
          `/${encodeURIComponent(username)}/roles/${encodeURIComponent(subject)}`,
          roles,
        ).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            toast.error("Error while setting roles", { description: text })
            return Promise.reject(text)
          }
          toast.success("Updated roles successfully")
        })
      },
    },
    self: {
      ...createBase(f, `${apiBase}/self`),
      async followers(): Promise<{ username: string; displayName: string }[]> {
        const response = await this.get(`/followers`)
        if (!response.ok) {
          return []
        }
        return response.json()
      },
      async following(): Promise<{ username: string; displayName: string }[]> {
        const response = await this.get(`/following`)
        if (!response.ok) {
          return []
        }
        return response.json()
      },
      async updateStream({ title, game }: { title?: string; game?: string }) {
        await this.postJSON("/stream/update", { title, game })
      },
      async getModeration(): Promise<{
        moderation: { duration: number | null; start: number; target: string }[]
        words: string
      }> {
        const response = await this.get("/stream/moderation")
        if (!response.ok) {
          return { moderation: [], words: "" }
        }
        return response.json()
      },
      async updateModerationWords(words: string): Promise<void> {
        await this.post("/stream/moderation/words", words).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            toast.error("Error while updating content filtering settings", { description: text })
            return Promise.reject(text)
          }
          toast.success("Updated content filtering settings successfully")
        })
      },
    },
    auth: {
      ...createBase(f, `${apiBase}/auth`),
      async available(username: string) {
        return (await this.get(`/available/${encodeURIComponent(username)}`)).status === 200
      },
      async signup(username: string, password: string, reenter: string) {
        await this.postJSON("/signup", { username, password, reenter }).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            toast.error("Error while signing up", { description: text })
            return Promise.reject(text)
          }
        })
      },
      async user(): Promise<User | null> {
        const response = await this.get("/user")
        if (response.status === 401) {
          return null
        }
        const { username, displayName, colour, streamToken } = await response.json()
        return { username, displayName, colour, streamToken } satisfies User
      },
      async login(username: string, password: string) {
        await this.postJSON("/login", { username, password }).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            toast.error("Error while logging in", { description: text })
            return Promise.reject(text)
          }
        })
      },
      async update(data: { username?: string; displayName?: string; colour?: number }) {
        await this.postJSON("/update", data).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            toast.error("Error while updating account", { description: text })
            return Promise.reject(text)
          }
        })
      },
      async updateStreamToken() {
        await this.post("/update/stream-token")
      },
      async updateAvatar(avatar: Blob) {
        const form = new FormData()
        form.append("avatar", avatar)
        await this.post("/update/avatar", form).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            toast.error("Error while updating profile picture", { description: text })
            return Promise.reject(text)
          }
        })
      },
      async updatePassword(currentPassword: string, newPassword: string, reenterPassword: string) {
        await this.postJSON("/update/password", {
          currentPassword,
          newPassword,
          reenterPassword,
        }).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            toast.error("Error while updating password", { description: text })
            return Promise.reject(text)
          }
        })
      },
    },
    roles: {
      ...createBase(f, `${apiBase}/roles`),
      async list(): Promise<{ id: number; name: string }[]> {
        return (await this.get("/")).json()
      },
      icon(id: number) {
        return this.resolve(`/${id}/icon`)
      },
    },
    stream: {
      ...createBase(f, `${apiBase}/stream`),
      async homepage(): Promise<string[]> {
        return (await this.get("/homepage")).json()
      },
    },
  }
}

export const server = serverWithFetch(fetch)

export const coloursByShade = (
  shade: "50" | "100" | "200" | "300" | "400" | "500" | "600" | "700" | "800" | "900" | "950",
) =>
  [
    tailwindColours.red,
    tailwindColours.orange,
    tailwindColours.amber,
    tailwindColours.yellow,
    tailwindColours.lime,
    tailwindColours.green,
    tailwindColours.emerald,
    tailwindColours.teal,
    tailwindColours.cyan,
    tailwindColours.sky,
    tailwindColours.blue,
    tailwindColours.indigo,
    tailwindColours.violet,
    tailwindColours.purple,
    tailwindColours.fuchsia,
    tailwindColours.pink,
    tailwindColours.rose,
  ].map((color) => color[shade])
export const colours = coloursByShade(500)

export function parseMessage(
  message: string,
  emotes: { [key: string]: [string, boolean] },
): Fragment[] {
  const fragments = message.matchAll(/\S+|\s/gy).map(([match]) => {
    if (/^\s*$/y.test(match)) {
      return { type: "text" as const, text: match }
    }
    const emote = emotes[match]
    if (emote) {
      const [url, zeroWidth] = emote
      return { type: "emote" as const, name: match, url, zeroWidth }
    }
    return { type: "text" as const, text: match }
  })
  const result = []
  const currentEmoteStack = []
  const drain = () => {
    if (currentEmoteStack.length == 1) {
      result.push(currentEmoteStack[0])
    } else if (currentEmoteStack.length > 1) {
      result.push({ type: "emote-stack", emotes: [...currentEmoteStack] })
    }
    currentEmoteStack.splice(0)
  }
  while (true) {
    const next = fragments.next()
    if (!next.value) break
    switch (next.value.type) {
      case "text":
        if (currentEmoteStack.length && /^\s*$/y.test(next.value.text)) break
        drain()
        result.push(next.value)
        break
      case "emote":
        if (!next.value.zeroWidth) {
          drain()
        }
        currentEmoteStack.push(next.value)
        break
    }
  }
  drain()
  return result
}

export function useElapsed(start: () => number | null) {
  const get = (start: number | null) =>
    start ? DateTime.fromSeconds(start).diffNow().negate().toFormat("hh:mm:ss") : null
  let elapsed: Date | null = $state(get(start()))
  onMount(() => {
    const interval = setInterval(() => {
      elapsed = get(start())
    }, 1000)
    return () => clearInterval(interval)
  })
  return () => elapsed
}

export function useNow(delay: number = 1000) {
  const now: SvelteDate = new SvelteDate()
  onMount(() => {
    const interval = setInterval(() => {
      now.setTime(Date.now())
    }, delay)
    return () => clearInterval(interval)
  })
  return () => now
}

class Moderation {
  sources: [string, string][] = $state([])
  words: { value: string } = $state({ value: "" })
  links: { block: boolean; warn: boolean } = $state({ block: false, warn: true })
  regexes = $derived(
    this.sources.flatMap(([source, flags]) => {
      try {
        return [new RegExp(source, flags)]
      } catch {
        return []
      }
    }),
  )
  constructor() {
    const item = localStorage.getItem("moderation")
    if (!item) return
    try {
      const { sources, words, links } = JSON.parse(item)
      this.sources = sources
      this.words = { value: words }
      this.links = links
    } catch {
      // keep initial state
    }
  }
}

export function useModeration() {
  const moderation = new Moderation()
  const match = (input: string) => {
    const words = input.split(/\s+/)
    return (
      moderation.regexes.some((regex) => !regex.test("") && regex.exec(input))
      || moderation.words.value
        .split(/\n|,/)
        .some(
          (word) =>
            word.trim()
            && words.some((other) =>
              wildcardMatch(word.trim(), { flags: "i", separator: false })(other),
            ),
        )
    )
  }
  $effect(() => {
    localStorage.setItem(
      "moderation",
      JSON.stringify({
        sources: moderation.sources,
        words: moderation.words.value,
        links: moderation.links,
      }),
    )
  })
  return { sources: moderation.sources, words: moderation.words, links: moderation.links, match }
}

export const isURL = (text: string) => {
  try {
    // eslint-disable-next-line svelte/prefer-svelte-reactivity
    const url = new URL(text)
    return ["http:", "https:"].includes(url.protocol)
  } catch {
    return false
  }
}
