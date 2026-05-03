<script lang="ts">
  import { invalidateAll } from "$app/navigation"
  import { resolve } from "$app/paths"
  import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "$lib/components/ui/empty"
  import { server } from "$lib/utils.svelte.js"
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
  {#each streams as { username, title, game, viewers } (username)}
    <a
      class="flex flex-col gap-2"
      href={resolve("/(main)/@[username=user]/watch", { username })}
      data-sveltekit-reload
    >
      <img
        src={server.user.streamPreview(username)}
        alt={title}
        class="w-80 rounded-md aspect-video"
      />
      <div class="flex flex-col">
        <div class="font-bold">{title}</div>
        <div class="text-sm text-muted-foreground">
          {game} · {viewers} viewers
        </div>
      </div>
    </a>
  {:else}
    <Empty>
      <EmptyHeader>
        <EmptyTitle>No one is currently live.</EmptyTitle>
        <EmptyDescription>Stream now to connect with people all over Inter.</EmptyDescription>
      </EmptyHeader>
    </Empty>
  {/each}
</main>
