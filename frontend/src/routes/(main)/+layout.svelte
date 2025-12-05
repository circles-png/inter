<script lang="ts">
  import { page } from "$app/state"
  import Logo from "$lib/components/logo.svelte"
  import { AvatarImage, AvatarFallback, Avatar } from "$lib/components/ui/avatar"
  import { Button } from "$lib/components/ui/button"
  import {
    Item,
    ItemActions,
    ItemContent,
    ItemDescription,
    ItemMedia,
    ItemTitle,
  } from "$lib/components/ui/item"
  import {
    SidebarProvider,
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarFooter,
    SidebarTrigger,
    SidebarHeader,
    SidebarGroupLabel,
    SidebarGroupContent,
  } from "$lib/components/ui/sidebar"
  import { Skeleton } from "$lib/components/ui/skeleton"
  import context from "$lib/context.svelte"
  import { getApiEndpoint } from "$lib/utils.svelte"
  import "../../app.css"
  import Settings from "@lucide/svelte/icons/settings"

  const { children } = $props()
  let sidebarOpen = $state(false)
  $effect(() => {
    context.user = fetch(getApiEndpoint(page.url.hostname, "http", "auth/user"), {
      method: "GET",
      credentials: "same-origin",
    }).then(async (response) => {
      if (response.status === 401) {
        return null
      }
      if (response.status === 500) {
        cookieStore.delete("session_token")
        return null
      }
      const { username, displayName, colour, avatarUrl } = await response.json()
      return { username, displayName, avatar: avatarUrl, colour, roles: [] }
    })
  })
</script>

<SidebarProvider class="flex grow" bind:open={sidebarOpen}>
  <Sidebar collapsible="icon">
    <SidebarHeader class="overflow-hidden">
      <div class="flex gap-4 items-center">
        <Logo class="shrink-0" />
        {#await context.user}
          <div class="flex gap-2 items-center">
            <Skeleton class="size-8" />
            <div class="flex flex-col gap-1">
              <Skeleton class="w-20 h-3" />
              <Skeleton class="w-15 h-3" />
            </div>
          </div>
        {:then user}
          {#if user}
            <Item size="xs" class="flex-nowrap grow">
              <ItemMedia>
                <Avatar class="*:rounded-lg size-8">
                  <AvatarImage src={user.avatar} alt="User avatar" />
                  <AvatarFallback><Logo class="fill-muted-foreground size-6" /></AvatarFallback>
                </Avatar>
              </ItemMedia>
              <ItemContent class="gap-0">
                <ItemTitle>{user.displayName ?? user.username}</ItemTitle>
                {#if user.displayName}
                  <ItemDescription>{user.username}</ItemDescription>
                {/if}
              </ItemContent>
              <ItemActions>
                <Button variant="secondary" size="icon-sm">
                  <Settings />
                </Button>
              </ItemActions>
            </Item>
          {/if}
        {/await}
      </div>
    </SidebarHeader>
    <SidebarContent class="overflow-hidden">
      <SidebarGroup>
        <SidebarGroupLabel>label</SidebarGroupLabel>
        <SidebarGroupContent>c</SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
    <SidebarFooter class="overflow-hidden">
      <div class="flex items-center gap-4">
        <SidebarTrigger />
        {#await context.user}
          <Skeleton class="w-full h-8" />
        {:then user}
          {#if user}
            <Button
              variant="secondary"
              href="/"
              class="grow"
              onclick={() => {
                cookieStore.delete("session_token")
                context.user = Promise.resolve(null)
              }}
            >
              Log out
            </Button>
          {:else}
            <Button variant="secondary" href="/login" class="grow">Log in</Button>
            <Button href="/signup" class="grow">Sign up</Button>
          {/if}
        {/await}
      </div>
    </SidebarFooter>
  </Sidebar>
  {@render children()}
</SidebarProvider>
