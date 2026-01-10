<script lang="ts">
  import UserItem from "../../lib/components/UserItem.svelte"

  import Logo from "$lib/components/logo.svelte"
  import { AvatarFallback, Avatar, AvatarImage } from "$lib/components/ui/avatar"
  import { Button } from "$lib/components/ui/button"
  import type { ButtonSize } from "$lib/components/ui/button"
  import { ItemActions } from "$lib/components/ui/item"
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
  import Settings from "@lucide/svelte/icons/settings"
  import { server } from "$lib/utils.svelte.js"
  import { resolve } from "$app/paths"
  import { invalidateAll } from "$app/navigation"
  import SlidersVertical from "@lucide/svelte/icons/sliders-vertical"
  import Home from "@lucide/svelte/icons/home"
  import { page } from "$app/state"
  import { cn } from "$lib/utils"
  import { IsMobile } from "$lib/hooks/is-mobile.svelte"
  import * as AvatarGroup from "$lib/components/ui/avatar-group"
  import { useSidebar } from "$lib/components/ui/sidebar"
  import { Tooltip, TooltipContent, TooltipTrigger } from "$lib/components/ui/tooltip"

  const { children, data } = $props()
  let isMobile = new IsMobile()
</script>

<SidebarProvider class="flex grow">
  <Sidebar collapsible="icon" variant="floating">
    <SidebarHeader class="overflow-clip">
      <SidebarMenu>
        <SidebarMenuItem class="flex items-center gap-2 p-2 md:p-0">
          {#if !isMobile.current}
            <Tooltip>
              <TooltipTrigger>
                {#snippet child({ props })}
                  <Button href={resolve("/")} variant="ghost" size="icon" {...props}>
                    <Logo class="size-9" />
                  </Button>
                {/snippet}
              </TooltipTrigger>
              <TooltipContent>Go to home page</TooltipContent>
            </Tooltip>
          {/if}
          <UserItem user={data.user}>
            {#if !isMobile.current}
              <ItemActions>
                <Tooltip>
                  <TooltipTrigger>
                    {#snippet child({ props })}
                      <Button variant="secondary" size="icon" href="/settings" {...props}>
                        <Settings />
                      </Button>
                    {/snippet}
                  </TooltipTrigger>
                  <TooltipContent side="right">Change account and chat settings</TooltipContent>
                </Tooltip>
              </ItemActions>
            {/if}
          </UserItem>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarHeader>
    <SidebarContent>
      {#if data.user}
        {#if !isMobile.current}
          <SidebarGroup>
            <SidebarGroupLabel>Your stream</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton size="lg" tooltipContent="Manage your stream">
                    {#snippet child({ props })}
                      <a href={resolve("/(main)/dashboard")} {...props}>
                        <div class="size-8 bg-muted p-2 rounded-md">
                          <SlidersVertical class="size-4" />
                        </div>
                        Dashboard
                      </a>
                    {/snippet}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        {/if}
        <SidebarGroup>
          <SidebarGroupLabel>Following</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {#each data.following as followee (followee.username)}
                <SidebarMenuItem>
                  <SidebarMenuButton size="lg">
                    {#snippet tooltipContent()}
                      {#if followee.displayName}
                        {followee.displayName} (@{followee.username})
                      {:else}
                        @{followee.username}
                      {/if}
                    {/snippet}
                    {#snippet child({ props })}
                      <a
                        href={resolve("/(main)/@[username=user]", { username: followee.username })}
                        {...props}
                      >
                        <Avatar class="size-8">
                          <AvatarImage
                            src={server.user.avatar(followee.username)}
                            alt={followee.username}
                          />
                          <AvatarFallback>
                            <Logo class="fill-muted-foreground size-6" />
                          </AvatarFallback>
                        </Avatar>
                        {followee.displayName || `@${followee.username}`}
                        {#if followee.displayName}
                          <span class="text-muted-foreground">@{followee.username}</span>
                        {/if}
                      </a>
                    {/snippet}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              {/each}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      {/if}
    </SidebarContent>
    <SidebarFooter class="overflow-clip">
      <SidebarMenu>
        <SidebarMenuItem>
          <div class="flex items-center gap-3">
            {#if !isMobile.current}
              <SidebarTrigger />
            {/if}
            {@render authButtons()}
          </div>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarFooter>
    <SidebarRail />
  </Sidebar>
  <div class="flex flex-col grow min-w-0">
    {@render header()}
    {@render children()}
    <div
      class="md:hidden grid auto-cols-[4em] grid-flow-col p-2 justify-between *:text-[10px] border-t"
    >
      <Button
        variant="ghost"
        href="/"
        class={cn(
          "flex flex-col h-auto px-0!",
          page.url.pathname === "/" || "text-muted-foreground",
        )}
      >
        <Home class="size-6" />
        Home
      </Button>
      {#if data.user}
        <Button
          variant="ghost"
          href="/dashboard"
          class={cn(
            "flex flex-col h-auto px-0!",
            page.url.pathname === "/dashboard" || "text-muted-foreground",
          )}
        >
          <SlidersVertical class="size-6" />
          Dashboard
        </Button>
        <Button
          variant="ghost"
          href={resolve("/(main)/@[username=user]", { username: data.user.username })}
          class={cn(
            "flex flex-col h-auto px-0!",
            page.url.pathname === `/@${data.user.username}` || "text-muted-foreground",
          )}
        >
          <Avatar class="size-6">
            <AvatarImage src={server.user.avatar(data.user.username)} alt={data.user.username} />
            <AvatarFallback><Logo class="fill-muted-foreground" /></AvatarFallback>
          </Avatar>
          Profile
        </Button>
      {/if}
      <Button
        variant="ghost"
        href="/settings"
        class={cn(
          "flex flex-col h-auto px-0!",
          page.url.pathname === "/settings" || "text-muted-foreground",
        )}
      >
        <Settings class="size-6" />
        Settings
      </Button>
    </div>
  </div>
</SidebarProvider>

{#snippet header()}
  {@const sidebar = useSidebar()}
  <div class="flex p-2 gap-2 md:hidden">
    <div class="flex p-2 bg-sidebar rounded-lg border grow justify-between">
      <Logo wordmark />
      <Button
        onclick={() => sidebar.toggle()}
        variant="ghost"
        class="bg-transparent! px-1 py-0 h-8"
      >
        <AvatarGroup.Root>
          <AvatarGroup.Member class="ring-sidebar"></AvatarGroup.Member>
          {#each data.following.slice(0, 3) as followee (followee.username)}
            <AvatarGroup.Member class="ring-sidebar">
              <AvatarGroup.MemberImage
                src={server.user.avatar(followee.username)}
                alt={followee.username}
              />
              <AvatarGroup.MemberFallback>
                <Logo class="fill-muted-foreground size-4" />
              </AvatarGroup.MemberFallback>
            </AvatarGroup.Member>
          {/each}
        </AvatarGroup.Root>
      </Button>
    </div>
  </div>
{/snippet}

{#snippet authButtons(size: ButtonSize = undefined)}
  {#if data.user}
    <Button
      variant="secondary"
      href="/"
      class="grow"
      onclick={async () => {
        await cookieStore.delete("session_token")
        await invalidateAll()
      }}
      {size}
    >
      Log out
    </Button>
  {:else}
    <Button variant="secondary" href="/login" class="grow" {size}>Log in</Button>
    <Button href="/signup" class="grow" {size}>Sign up</Button>
  {/if}
{/snippet}
