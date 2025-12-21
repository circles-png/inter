<script lang="ts">
  import { Toaster } from "$lib/components/ui/sonner"
  import CircleAlert from "@lucide/svelte/icons/circle-alert"
  import "../app.css"
  import { userContext, userUpdateContext } from "$lib/context.svelte"
  import { server } from "$lib/utils.svelte"
  const { children } = $props()

  $effect(() => {
    if (!userContext.user) return
    userUpdateContext.userUpdate = server.auth
      .update({
        username: userContext.user.username,
        displayName: userContext.user.displayName,
        colour: userContext.user.colour,
      })
      .then(() => {
        userUpdateContext.userUpdate = null
      })
  })
</script>

<Toaster richColors closeButton {errorIcon} />

{@render children()}

{#snippet errorIcon()}
  <CircleAlert class="size-5" />
{/snippet}
