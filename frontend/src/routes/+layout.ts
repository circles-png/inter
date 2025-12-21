import { userContext } from "$lib/context.svelte"
import { serverWithFetch } from "$lib/utils.svelte"
import type { LayoutLoad } from "./$types"

export const ssr = false

export const load: LayoutLoad = async ({ fetch }) => {
  userContext.user = await serverWithFetch(fetch).auth.user()
}
