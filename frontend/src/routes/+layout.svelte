<script lang="ts">
  import { Toaster } from "$lib/components/ui/sonner"
  import CircleAlert from "@lucide/svelte/icons/circle-alert"
  import "../app.css"
  import { getApiEndpoint } from "$lib/utils.svelte"
  import { toast } from "svelte-sonner"
  import { userContext, userUpdateContext } from "$lib/context.svelte"
  import { onMount } from "svelte"
  const { children } = $props()

  userContext.user = fetch(getApiEndpoint("http", "auth/user"), {
    method: "GET",
    credentials: "same-origin",
  }).then(async (response) => {
    if (response.status === 401) {
      return null
    } else if (response.status === 500) {
      cookieStore.delete("session_token")
      return null
    }
    const { username, displayName, colour, avatarUrl } = await response.json()
    return { username, displayName, avatar: avatarUrl, colour, roles: [] }
  })

  let mounted = false

  $effect(() => {
    userContext.user
    if (!mounted) return
    userContext.user.then((user) => {
      if (!user) return
      userUpdateContext.userUpdate = fetch(getApiEndpoint("http", "auth/update"), {
        method: "POST",
        body: JSON.stringify({ username: user.username, displayName: user.displayName }),
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
      }).then(async (response) => {
        if (!response.ok) {
          const text = await response.text()
          toast.error("Error while updating profile", { description: text })
          return Promise.reject(text)
        }
        toast.success("Profile updated successfully")
        userUpdateContext.userUpdate = null
      })
    })
  })

  onMount(() => {
    mounted = true
  })
</script>

<Toaster richColors closeButton {errorIcon} />

{@render children()}

{#snippet errorIcon()}
  <CircleAlert class="size-5" />
{/snippet}
