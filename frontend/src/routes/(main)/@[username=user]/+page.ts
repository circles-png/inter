import { serverWithFetch } from "$lib/utils.svelte"
import type { PageLoad } from "./$types"

export const load: PageLoad = async ({ fetch, params }) => {
  return { ...(await serverWithFetch(fetch).user.user(params.username)) }
}
