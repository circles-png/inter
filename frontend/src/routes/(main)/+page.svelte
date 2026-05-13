<script lang="ts">
  import { invalidateAll } from "$app/navigation"
  import { resolve } from "$app/paths"
  import { Avatar, AvatarFallback, AvatarImage } from "$lib/components/ui/avatar"
  import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "$lib/components/ui/empty"
  import { server } from "$lib/utils.svelte.js"
  import User from "@lucide/svelte/icons/user"
  import { onMount } from "svelte"
  let { data } = $props()
  let streams = $derived(data.streams)
  onMount(() => {
    const interval = setInterval(async () => {
      await invalidateAll()
    }, 5000)
    return () => {
      clearInterval(interval)
    }
  })
</script>

<main class="p-2 flex flex-col gap-2 overflow-y-auto grow pr-0">
  {#if streams.length > 0}
    {#if streams.some(({ recommended }) => recommended)}
      <h1 class="font-bold text-xl">Recommended for you</h1>
      {#each streams.filter(({ recommended }) => recommended) as stream (stream.username)}
        {@render streamCard(stream)}
      {/each}
    {/if}
    {#each new Set(streams.map((stream) => stream.game).filter((game) => game)) as game (game)}
      <h1 class="text-xl">
        In <span class="font-bold">{game}</span>
      </h1>
      {#each streams.filter((stream) => stream.game === game) as stream (stream.username)}
        {@render streamCard(stream)}
      {/each}
    {/each}
    <h1 class="font-bold text-xl">All streams</h1>
    {#each streams as stream (stream.username)}
      {@render streamCard(stream)}
    {/each}
  {:else}
    <Empty>
      <EmptyHeader>
        <EmptyTitle>No one is currently live.</EmptyTitle>
        <EmptyDescription>Stream now to connect with people all over Inter.</EmptyDescription>
      </EmptyHeader>
    </Empty>
  {/if}
</main>

{#snippet streamCard({
  username,
  title,
  game,
  viewers,
}: {
  username: string
  title: string
  game: string
  viewers: number | null
})}
  <a
    class="flex flex-col gap-2 w-80"
    href={resolve("/(main)/@[username=user]/watch", { username })}
    data-sveltekit-reload
  >
    <img src={server.user.streamPreview(username)} alt={title} class="rounded-md aspect-video" />
    <div class="flex gap-2">
      <div class="flex flex-col">
        <Avatar class="size-8">
          <AvatarImage src={server.user.avatar(username)} alt={username} />
          <AvatarFallback class="bg-muted" />
        </Avatar>
      </div>
      <div class="flex flex-col grow">
        {#await server.user.user(username) then user}
          <div class="font-bold">{user.displayName || `@${username}`}</div>
          {title}
          <div class="text-sm text-muted-foreground">
            {game}
          </div>
        {/await}
      </div>
      <div>
        <div class="flex md:gap-2 items-center text-red-400 font-mono text-xs">
          <User class="h-4" />
          {viewers ?? 0}
        </div>
      </div>
    </div>
  </a>
{/snippet}
