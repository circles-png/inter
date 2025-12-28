import type { Fragment } from "../models/message"
import type { User } from "../models/user"
import tailwindColours from "tailwindcss/colors"
import { toast } from "svelte-sonner"

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
  const response = server.auth.available(username)
  if (response.status === 409) {
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
    async emotes(): Promise<{ [key: string]: [string, boolean] }> {
      return (await this.get("/emotes")).json() // TODO cache these
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
      async stream(
        username: string,
      ): Promise<{ title: string; game: string; start: number | null; viewers: number | null }> {
        return (await this.get(`/${encodeURIComponent(username)}/stream`)).json()
      },
      streamPreview(username: string) {
        return this.resolve(`/${encodeURIComponent(username)}/stream/preview`)
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
        const { username, displayName, colour, streamToken, roles } = await response.json()
        return { username, displayName, colour, streamToken, roles } satisfies User
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
      async updatePassword(current: string, newPassword: string, reenter: string) {
        await this.postJSON("/update/password", { current, newPassword, reenter }).then(
          async (response) => {
            if (!response.ok) {
              const text = await response.text()
              toast.error("Error while updating password", { description: text })
              return Promise.reject(text)
            }
          },
        )
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
  while (true) {
    const next = fragments.next()
    if (!next.value) break
    switch (next.value.type) {
      case "text":
        if (currentEmoteStack.length && /^\s*$/y.test(next.value.text)) {
          break
        }
        if (currentEmoteStack.length == 1) {
          result.push(currentEmoteStack[0])
        } else if (currentEmoteStack.length > 1) {
          result.push({ type: "emote-stack", emotes: [...currentEmoteStack] })
        }
        currentEmoteStack.splice(0)
        result.push(next.value)
        break
      case "emote":
        if (next.value.zeroWidth) {
          currentEmoteStack.push(next.value)
        } else {
          if (currentEmoteStack.length == 1) {
            result.push(currentEmoteStack[0])
          } else if (currentEmoteStack.length > 1) {
            result.push({ type: "emote-stack", emotes: [...currentEmoteStack] })
          }
          currentEmoteStack.splice(0)
          currentEmoteStack.push(next.value)
        }
        break
    }
  }
  if (currentEmoteStack.length == 1) {
    result.push(currentEmoteStack[0])
  } else if (currentEmoteStack.length > 1) {
    result.push({ type: "emote-stack", emotes: [...currentEmoteStack] })
  }
  return result
}
