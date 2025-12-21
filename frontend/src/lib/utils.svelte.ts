import type { User } from "../models/user"

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

export const server = {
  async fetch(url, init) {
    return fetch(
      this.resolve(url),
      { ...init, credentials: "same-origin", },
    )
  },
  async get(url: URL, headers?: HeadersInit) {
    return this.fetch(url, {
      method: "GET",
      headers,
    })
  },
  async post(url: URL, body?: BodyInit, headers?: HeadersInit) {
    return this.fetch(url, {
      method: "POST",
      body,
      headers,
    })
  },
  async postJSON(url: URL, data: unknown) {
    return this.post(url, JSON.stringify(data), {
      "Content-Type": "application/json",
    })
  },
  resolve(url: string) {
    return "/api/v1" + url
  },
  async random() {
    return (await this.get("/random")).text()
  },
  async avatar(username: string) {
    return this.get(`/avatar/${encodeURIComponent(username)}`)
  },
  async streamToken() {
    return (await this.get("/stream-token")).text()
  },
  auth: {
    async available(username: string) {
      return (await server.get(`/auth/available/${encodeURIComponent(username)}`)).status === 200
    },
    async signup(username: string, password: string, reenter: string) {
      await server.postJSON("/auth/signup", {
        username,
        password,
        reenter,
      })
    },
    async user(): Promise<User> {
      return (await server.get("/auth/user")).json()
    },
    async login(username: string, password: string) {
      await server.postJSON("/auth/login", {
        username,
        password,
      }).then(async (response) => {
        if (!response.ok) {
          const text = await response.text()
          toast.error("Error while logging in", { description: text })
          return Promise.reject(text)
        }
      })
    },
    async update(data: {
      username?: string,
      displayName?: string,
      colour?: string,
    }) {
      await server.postJSON("/auth/update", data).then(async (response) => {
        if (!response.ok) {
          const text = await response.text()
          toast.error("Error while updating account", { description: text })
          return Promise.reject(text)
        }
      })
    },
    async updateStreamToken() {
      await server.post("/auth/update/stream-token")
    },
    async updateAvatar(avatar: Blob) {
      const form = new FormData()
      form.append("avatar", avatar)
      await server.post("/auth/update/avatar", form).then(async (response) => {
        if (!response.ok) {
          const text = await response.text()
          toast.error("Error while updating profile picture", { description: text })
          return Promise.reject(text)
        }
      })
    },
    async updatePassword(current: string, newPassword: string, reenter: string) {
      await server.postJSON("/auth/update/password", {
        current,
        newPassword,
        reenter,
      }).then(async (response) => {
        if (!response.ok) {
          const text = await response.text()
          toast.error("Error while updating password", { description: text })
          return Promise.reject(text)
        }
      })
    }
  }
}
