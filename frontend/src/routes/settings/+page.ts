import { goto } from "$app/navigation"
import { resolve } from "$app/paths"
import type { PageLoad } from "./$types"

export const load: PageLoad = async ({ parent }) => {
  const { user } = await parent()
  if (!user) {
    await goto(resolve("/login"))
    return
  }
  return { user }
}
