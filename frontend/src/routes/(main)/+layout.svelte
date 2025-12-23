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
  import "../../app.css"
  import Settings from "@lucide/svelte/icons/settings"
  import { server } from "$lib/utils.svelte.js"
  import { resolve } from "$app/paths"
  import { invalidateAll } from "$app/navigation"

  const { children, data } = $props()
</script>

<SidebarProvider class="flex grow">
  <Sidebar collapsible="icon" variant="floating">
    <SidebarHeader class="overflow-clip">
      <SidebarMenu>
        <SidebarMenuItem class="flex items-center gap-2 *:last:grow">
          <a href={resolve("/")}>
            <Logo class="shrink-0" />
          </a>
          {#if data.user}
            <UserItem user={data.user}>
              <ItemActions>
                <Button variant="secondary" size="icon" href="/settings">
                  <Settings />
                </Button>
              </ItemActions>
            </UserItem>
          {/if}
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarHeader>
    <SidebarContent>
      {#if data.user}
        <SidebarGroup>
          <SidebarGroupLabel>Following</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {#each data.following as followee (followee.username)}
                <SidebarMenuItem>
                  <SidebarMenuButton size="lg">
                    {#snippet tooltipContent()}
                      {followee.displayName} (@{followee.username})
                    {/snippet}
                    {#snippet child({ props })}
                      <a
                        href={resolve("/(main)/@[username=user]", { username: followee.username })}
                        {...props}
                      >
                        <Avatar class="*:rounded-lg size-8">
                          <AvatarImage
                            src={server.user.avatar(followee.username)}
                            alt={followee.username}
                          />
                          <AvatarFallback
                            ><Logo class="fill-muted-foreground size-6" /></AvatarFallback
                          >
                        </Avatar>
                        {followee.displayName}
                        <span class="text-muted-foreground">@{followee.username}</span>
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
            <SidebarTrigger />
            {@render authButtons()}
          </div>
        </SidebarMenuItem>
      </SidebarMenu>
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
