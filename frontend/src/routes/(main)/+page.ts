import { serverWithFetch } from "$lib/utils.svelte"
import type { PageLoad } from "./$types"

export const load: PageLoad = async ({ fetch }) => {
  const server = serverWithFetch(fetch)
  return {
    streams: await Promise.all(
      (await server.stream.homepage()).map(async (username) => ({
        ...(await server.user.stream(username)),
        username,
      })),
    ),
  }
}
