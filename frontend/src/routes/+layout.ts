import { serverWithFetch } from "$lib/utils.svelte"
import type { LayoutLoad } from "./$types"

export const ssr = false

export const load: LayoutLoad = async ({ fetch }) => {
  const server = serverWithFetch(fetch)
  return { following: await server.self.following(), user: await server.auth.user() }
}
