import { page } from "$app/state"

export function getApiEndpoint(protocol: string, path: string, port: string = "5001"): string {
  return `${protocol}://${page.url.hostname}:${port}/api/v1/${path}`;
}

function debounce<A extends any[]>(f: (...args: A) => unknown, ms: number) {
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
  const response = await fetch(
    getApiEndpoint(
      "http",
      `auth/available/${encodeURIComponent(username)}`,
    ),
    { method: "GET" },
  )
  if (response.status === 409) {
    return "Username is already taken."
  }
  return null
}
