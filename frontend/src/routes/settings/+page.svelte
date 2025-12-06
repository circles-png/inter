<script>
  import Security from "./Security.svelte"
  import StreamTokens from "./StreamTokens.svelte"
  import Profile from "./Profile.svelte"
  import Logo from "$lib/components/logo.svelte"
  import { AvatarImage, AvatarFallback, Avatar } from "$lib/components/ui/avatar"
  import { Button } from "$lib/components/ui/button"
  import {
    Item,
    ItemMedia,
    ItemContent,
    ItemTitle,
    ItemDescription,
    ItemActions,
  } from "$lib/components/ui/item"
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
    SidebarRail,
  } from "$lib/components/ui/sidebar"
  import { Skeleton } from "$lib/components/ui/skeleton"
  import LogOut from "@lucide/svelte/icons/log-out"
  import CircleUser from "@lucide/svelte/icons/circle-user"
  import KeyRound from "@lucide/svelte/icons/key-round"
  import Lock from "@lucide/svelte/icons/lock"
  import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuGroup,
    DropdownMenuItem,
    DropdownMenuTrigger,
  } from "$lib/components/ui/dropdown-menu"
  import { userContext } from "$lib/context.svelte"
  import UserItem from "$lib/components/UserItem.svelte"

  let tab = $state("profile")
</script>

<SidebarProvider>
  <Sidebar collapsible="none">
    <SidebarContent>
      <SidebarGroup>
        <SidebarGroupLabel>Account</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {#each [{ icon: CircleUser, label: "Profile", value: "profile" }, { icon: KeyRound, label: "Stream tokens", value: "tokens" }, { icon: Lock, label: "Security", value: "security" }] as { icon: Icon, label, value }}
              <SidebarMenuItem class="flex items-center gap-2">
                <SidebarMenuButton
                  onclick={() => {
                    tab = value
                  }}
                  isActive={tab === value}
                >
                  <Icon />
                  {label}
                </SidebarMenuButton>
              </SidebarMenuItem>
            {/each}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
    <SidebarFooter>
      <div class="flex items-center gap-4">
        <UserItem>
          <ItemActions>
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button variant="secondary" size="icon-sm">
                  <LogOut />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent side="top" align="end">
                <DropdownMenuGroup>
                  <DropdownMenuItem
                    onclick={() => {
                      cookieStore.delete("session_token")
                      userContext.user = Promise.resolve(null)
                    }}
                  >
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          </ItemActions>
        </UserItem>
      </div>
    </SidebarFooter>
    <SidebarRail />
  </Sidebar>
  {#if tab === "profile"}
    <Profile />
  {:else if tab === "tokens"}
    <StreamTokens />
  {:else if tab === "security"}
    <Security />
  {/if}
</SidebarProvider>
