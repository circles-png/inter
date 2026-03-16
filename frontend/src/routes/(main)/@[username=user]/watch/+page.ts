import { serverWithFetch } from "$lib/utils.svelte"
import type { PageLoad } from "./$types"

export const load: PageLoad = async ({ fetch }) => {
  const server = serverWithFetch(fetch)
  return { emotes: await server.emotes(), roles: await server.roles.list() }
}
