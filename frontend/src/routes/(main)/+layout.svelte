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
  import { userContext } from "$lib/context.svelte"
  import "../../app.css"
  import Settings from "@lucide/svelte/icons/settings"
  import { server } from "$lib/utils.svelte.js"
  import { resolve } from "$app/paths"

  const { children, data } = $props()
</script>

<SidebarProvider class="flex grow">
  <Sidebar collapsible="icon" variant="floating">
    <SidebarHeader class="overflow-hidden">
      <div class="flex gap-4 items-center min-w-0">
        <a href={resolve("/")}>
          <Logo class="shrink-0" />
        </a>
        <UserItem>
          <ItemActions>
            <Button variant="secondary" size="icon" href="/settings">
              <Settings />
            </Button>
          </ItemActions>
        </UserItem>
      </div>
    </SidebarHeader>
    <SidebarContent class="overflow-hidden">
      <SidebarGroup>
        <SidebarGroupLabel>Following</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {#each data.following as followee (followee.username)}
              <SidebarMenuItem>
                <SidebarMenuButton size="lg">
                  {#snippet child({ props })}
                    <a
                      href={resolve("/(main)/@[username=user]", { username: followee.username })}
                      {...props}
                    >
                      <Avatar class="*:rounded-lg size-8">
                        <AvatarImage
                          src={server.user.avatar(followee.username)}
                          alt="User avatar"
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
    </SidebarContent>
    <SidebarFooter class="overflow-hidden">
      <div class="flex items-center gap-2">
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
  {#if userContext.user}
    <Button
      variant="secondary"
      href="/"
      class="grow"
      onclick={() => {
        cookieStore.delete("session_token")
        userContext.user = null
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
