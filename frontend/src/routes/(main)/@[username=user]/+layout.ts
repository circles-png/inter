import { serverWithFetch } from "$lib/utils.svelte"
import type { PageLoad } from "./$types"

export const load: PageLoad = async ({ fetch, params }) => {
  const server = serverWithFetch(fetch)
  return {
    profile: await server.user.user(params.username),
    stream: await server.user.stream(params.username),
    notify: await server.user.getNotify(params.username),
  }
}
