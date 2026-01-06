import { serverWithFetch } from "$lib/utils.svelte"
import type { PageLoad } from "./$types"

export const load: PageLoad = async ({ fetch, params }) => {
  const { username } = params
  const server = serverWithFetch(fetch)
  return {
    emotes: await server.emotes(),
    streamer: { ...(await server.user.user(username)), username: username },
    stream: await server.user.stream(username),
  }
}
