<script lang="ts">
  import { invalidateAll } from "$app/navigation"
  import { page } from "$app/state"
  import { Avatar, AvatarFallback, AvatarImage } from "$lib/components/ui/avatar"
  import { Button } from "$lib/components/ui/button"
  import { colours, server } from "$lib/utils.svelte"

  let { data } = $props()
  const following = $derived(data.following)
  const { displayName, colour } = $derived(data.user)
  const username = page.params.username || ""
</script>

<div class="flex flex-col p-2 gap-4">
  <div
    class="aspect-3/1 rounded-md border"
    style:background-color={colours[colour]}
    style:background-repeat="no-repeat"
  ></div>
  <div class="flex gap-4 border rounded-md p-4 items-center">
    <Avatar class="size-12">
      <AvatarImage src={server.user.avatar(username)} alt="User avatar" />
      <AvatarFallback class="bg-muted" />
    </Avatar>
    <div class="flex flex-col grow">
      <div class="font-bold">{displayName}</div>
      <div class="text-sm text-muted-foreground">@{username}</div>
    </div>
    {#if following.some((following) => following.username == username)}
      <Button
        onclick={async () => {
          server.user.unfollow(username)
          await invalidateAll()
        }}
      >
        Unfollow
      </Button>
    {:else}
      <Button
        onclick={async () => {
          server.user.follow(username)
          await invalidateAll()
        }}
      >
        Follow
      </Button>
    {/if}
  </div>
</div>
