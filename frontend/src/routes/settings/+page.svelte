<script lang="ts">
  import Security from "./Security.svelte"
  import StreamTokens from "./StreamTokens.svelte"
  import Profile from "./Profile.svelte"
  import { Button } from "$lib/components/ui/button"
  import { ItemActions } from "$lib/components/ui/item"
  import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarProvider,
    SidebarTrigger,
  } from "$lib/components/ui/sidebar"
  import LogOut from "@lucide/svelte/icons/log-out"
  import CircleUser from "@lucide/svelte/icons/circle-user"
  import KeyRound from "@lucide/svelte/icons/key-round"
  import Lock from "@lucide/svelte/icons/lock"
  import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
  } from "$lib/components/ui/dropdown-menu"
  import UserItem from "$lib/components/UserItem.svelte"
  import { goto, invalidateAll } from "$app/navigation"
  import { resolve } from "$app/paths"
  import { IsMobile } from "$lib/hooks/is-mobile.svelte"
  import MessagesSquare from "@lucide/svelte/icons/messages-square"
  import { type Component } from "svelte"
  import Moderation from "./Moderation.svelte"

  const tabs = [
    {
      name: "Account",
      requireUser: true,
      items: [
        {
          icon: CircleUser,
          label: "Profile",
          value: "profile",
          description: "Manage your public profile",
        },
        {
          icon: KeyRound,
          label: "Stream token",
          value: "token",
          description: "View and rotate stream tokens",
        },
        { icon: Lock, label: "Security", value: "security", description: "Change your password" },
      ],
    },
    {
      name: "Chat",
      requireUser: false,
      items: [
        {
          icon: MessagesSquare,
          label: "Moderation",
          value: "moderation",
          description: "Change your personal moderation settings",
        },
      ],
    },
  ]
  let { data } = $props()
  // svelte-ignore state_referenced_locally
  let tab = $state(data.user ? "profile" : "moderation")

  const isMobile = new IsMobile()
</script>

<SidebarProvider>
  <Sidebar collapsible={isMobile ? "offcanvas" : "none"} class="shrink-0">
    <SidebarContent>
      {#each tabs as { name, requireUser, items } (name)}
        {#if !requireUser || data.user}
          <SidebarGroup>
            <SidebarGroupLabel>{name}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {#each items as { icon: Icon, label, value, description } (label)}
                  {@render item(Icon, label, value, description)}
                {/each}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        {/if}
      {/each}
    </SidebarContent>
    {#if data.user}
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <UserItem user={data.user}>
              <ItemActions>
                <DropdownMenu>
                  <DropdownMenuTrigger>
                    {#snippet child({ props })}
                      <Button variant="secondary" size="icon" {...props}>
                        <LogOut />
                      </Button>
                    {/snippet}
                  </DropdownMenuTrigger>
                  <DropdownMenuContent side="top" align="end">
                    <DropdownMenuItem
                      onclick={async () => {
                        await cookieStore.delete("session_token")
                        await invalidateAll()
                        await goto(resolve("/"))
                      }}
                    >
                      Log out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </ItemActions>
            </UserItem>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    {/if}
  </Sidebar>
  <div class="flex flex-col grow">
    <div class="p-4 grow flex flex-col gap-2">
      <div class="md:hidden flex justify-between">
        <h1 class="text-2xl font-bold">
          {tabs.flatMap((tab) => tab.items).find(({ value }) => value === tab)?.label}
        </h1>
        <SidebarTrigger />
      </div>
      <h1 class="text-2xl font-bold hidden md:block">
        {tabs.flatMap((tab) => tab.items).find(({ value }) => value === tab)?.label}
      </h1>
      {#if data.user}
        {#if tab === "profile"}
          <Profile user={data.user} />
        {:else if tab === "token"}
          <StreamTokens user={data.user} />
        {:else if tab === "security"}
          <Security />
        {/if}
      {/if}
      {#if tab == "moderation"}
        <Moderation />
      {/if}
    </div>
  </div>
</SidebarProvider>

{#snippet item(Icon: Component, label: string, value: string, description: string)}
  <SidebarMenuItem>
    <SidebarMenuButton
      isActive={tab === value}
      tooltipContent={description}
      onclick={() => {
        tab = value
      }}
    >
      <Icon />
      {label}
    </SidebarMenuButton>
  </SidebarMenuItem>
{/snippet}
