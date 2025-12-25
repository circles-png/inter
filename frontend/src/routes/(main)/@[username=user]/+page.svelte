<script lang="ts">
  import { invalidateAll } from "$app/navigation"
  import { resolve } from "$app/paths"
  import { page } from "$app/state"
  import { Avatar, AvatarFallback, AvatarImage } from "$lib/components/ui/avatar"
  import { Button } from "$lib/components/ui/button"
  import { colours, server } from "$lib/utils.svelte"

  let { data } = $props()
  const user = $derived(data.user)
  const profile = $derived(data.profile)
  const following = $derived(data.following)
  const stream = $derived(data.stream)
  const username = $derived(page.params.username || "")
  const avatar = $derived(server.user.avatar(username))
</script>

<div class="flex flex-col p-2 gap-4">
  <div
    class="aspect-3/1 rounded-md border"
    style:background-color={colours[profile.colour]}
    style:background-repeat="no-repeat"
  ></div>
  {#key avatar}
    <div class="flex gap-4 border rounded-md p-4 items-center">
      <Avatar class="size-16">
        <AvatarImage src={avatar} alt={username} />
        <AvatarFallback class="bg-muted" />
      </Avatar>
      <div class="flex flex-col grow">
        <div class="font-bold">{profile.displayName || `@${username}`}</div>
        {#if profile.displayName}
          <div class="text-sm text-muted-foreground">@{username}</div>
        {/if}
        <div class="text-sm flex gap-4">
          <div>{profile.followers} followers</div>
          <div>{profile.following} following</div>
        </div>
      </div>
      <Button href={resolve("/(main)/@[username=user]/watch", { username })}>
        {#if stream.viewers}
          Watch
        {:else}
          Chat
        {/if}
      </Button>
      {#if user && username != user.username}
        {#if following.some((following) => following.username == username)}
          <Button
            onclick={async () => {
              server.user.unfollow(username)
              await invalidateAll()
            }}
            variant="outline"
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
      {/if}
    </div>
  {/key}
  {#if stream.viewers}
    <div class="flex flex-col gap-4">
      <div class="font-bold text-lg">Currently Streaming</div>
      <a class="flex flex-col gap-2" href={resolve("/(main)/@[username=user]/watch", { username })}>
        <img src={server.user.streamPreview(username)} alt={stream.title} class="w-80 rounded-md" />
        <div class="flex flex-col">
          <div class="font-bold">{stream.title}</div>
          <div class="text-sm text-muted-foreground">
            {stream.game} · {stream.viewers} viewers
          </div>
        </div>
      </a>
    </div>
  {/if}
</div>
