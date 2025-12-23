import { userContext } from "$lib/context.svelte"
import { serverWithFetch } from "$lib/utils.svelte"
import type { LayoutLoad } from "./$types"

export const ssr = false

export const load: LayoutLoad = async ({ fetch }) => {
  const server = serverWithFetch(fetch)
  userContext.user = await server.auth.user()
  return { following: await server.self.following() }
}
