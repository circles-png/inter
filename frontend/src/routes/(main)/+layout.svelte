<script lang="ts">
  import Logo from "$lib/components/logo.svelte"
  import { AvatarImage, AvatarFallback, Avatar } from "$lib/components/ui/avatar"
  import { Button } from "$lib/components/ui/button"
  import type { ButtonSize } from "$lib/components/ui/button"
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
    SidebarRail,
    SidebarMenuItem,
    SidebarMenu,
    SidebarMenuButton,
  } from "$lib/components/ui/sidebar"
  import { Skeleton } from "$lib/components/ui/skeleton"
  import context from "$lib/context.svelte"
  import "../../app.css"
  import Settings from "@lucide/svelte/icons/settings"

  const { children } = $props()
</script>

<SidebarProvider class="flex grow">
  <Sidebar collapsible="icon" variant="floating">
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
                  <ItemDescription>@{user.username}</ItemDescription>
                {/if}
              </ItemContent>
              <ItemActions>
                <Button variant="secondary" size="icon-sm" href="/settings">
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
        <SidebarGroupLabel>Following</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {#each { length: 3 }}
              <SidebarMenuItem>
                <SidebarMenuButton size="lg">
                  <Avatar class="*:rounded-lg size-8">
                    <AvatarFallback><Logo class="fill-muted-foreground size-6" /></AvatarFallback>
                  </Avatar>
                  Streamer
                </SidebarMenuButton>
              </SidebarMenuItem>
            {/each}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
    <SidebarFooter class="overflow-hidden">
      <div class="flex items-center gap-4">
        <SidebarTrigger />
        {@render authButtons()}
      </div>
    </SidebarFooter>
    <SidebarRail />
  </Sidebar>
  <div class="flex flex-col grow min-w-0">
    {@render children()}
    {@render header()}
  </div>
</SidebarProvider>

{#snippet header()}
  <div class="flex p-2 gap-2 md:hidden">
    <div class="flex p-2 bg-sidebar border-sidebar-border rounded-lg border">
      <SidebarTrigger />
    </div>
    <div class="flex p-2 bg-sidebar border-sidebar-border rounded-lg border grow justify-between">
      <Logo wordmark />
      <div class="flex gap-2">{@render authButtons("sm")}</div>
    </div>
  </div>
{/snippet}

{#snippet authButtons(size: ButtonSize = undefined)}
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
        {size}
      >
        Log out
      </Button>
    {:else}
      <Button variant="secondary" href="/login" class="grow" {size}>Log in</Button>
      <Button href="/signup" class="grow" {size}>Sign up</Button>
    {/if}
  {/await}
{/snippet}
