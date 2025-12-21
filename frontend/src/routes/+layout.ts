import { userContext } from "$lib/context.svelte"
import type { LayoutLoad } from "./$types"

export const ssr = false

export const load: LayoutLoad = async ({ fetch }) => {
  userContext.user = await fetch("/api/v1/auth/user", {
    method: "GET",
    credentials: "same-origin",
  }).then(async (response) => {
    if (response.status === 401) {
      return null
    } else if (response.status === 500) {
      cookieStore.delete("session_token")
      return null
    }
    const { username, displayName, avatarUrl, colour, streamToken, roles } = await response.json()
    return { username, displayName, avatar: avatarUrl, colour, streamToken, roles } satisfies User
  })
}
