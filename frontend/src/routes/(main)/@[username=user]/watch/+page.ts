import { serverWithFetch } from "$lib/utils.svelte"

export const load: PageLoad = async ({ fetch, params }) => {
  const server = serverWithFetch(fetch)
  return {
    emotes: await server.emotes(),
    streamer: { ...(await server.user.user(params.username)), username: params.username },
  }
}
