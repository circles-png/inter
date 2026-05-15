import { goto } from "$app/navigation"
import { resolve } from "$app/paths"
import { serverWithFetch } from "$lib/utils.svelte"
import type { PageLoad } from "./$types"

export const load: PageLoad = async ({ parent, fetch }) => {
  const { user } = await parent()
  if (!user) {
    await goto(resolve("/login"))
    return
  }
  const server = serverWithFetch(fetch)
  return {
    user,
    stream: await server.user.stream(user.username),
    ...(await server.user.user(user.username)),
    notify: await server.user.getNotify(user.username),
    roles: await server.roles.list(),
  }
}
