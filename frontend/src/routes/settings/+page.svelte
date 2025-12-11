<script>
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
    SidebarRail,
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
  import { userContext } from "$lib/context.svelte"
  import UserItem from "$lib/components/UserItem.svelte"
  import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
  } from "$lib/components/ui/tooltip"
  import { goto } from "$app/navigation"
  import { resolve } from "$app/paths"
  import { IsMobile } from "$lib/hooks/is-mobile.svelte"

  let tab = $state("profile")
  const tabs = [
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
  ]

  const isMobile = new IsMobile()
</script>

<SidebarProvider>
  <Sidebar collapsible={isMobile ? "offcanvas" : "none"} class="shrink-0">
    <SidebarContent>
      <SidebarGroup>
        <SidebarGroupLabel>Account</SidebarGroupLabel>
        <SidebarGroupContent>
          <TooltipProvider>
            <SidebarMenu>
              {#each tabs as { icon: Icon, label, value, description } (label)}
                <Tooltip>
                  <TooltipTrigger
                    class="flex items-center gap-2"
                    onclick={() => {
                      tab = value
                    }}
                  >
                    {#snippet child({ props })}
                      <SidebarMenuItem>
                        <SidebarMenuButton isActive={tab === value} {...props}>
                          <Icon />
                          {label}
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    {/snippet}
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    {description}
                  </TooltipContent>
                </Tooltip>
              {/each}
            </SidebarMenu>
          </TooltipProvider>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
    <SidebarFooter>
      <div class="flex items-center gap-4">
        <UserItem>
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
                    cookieStore.delete("session_token")
                    userContext.user = Promise.resolve(null)
                    await goto(resolve("/"))
                  }}
                >
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </ItemActions>
        </UserItem>
      </div>
    </SidebarFooter>
    <SidebarRail />
  </Sidebar>
  <div class="flex flex-col grow">
    {#if isMobile}
      <SidebarTrigger />
    {/if}
    {#if tab === "profile"}
      <Profile />
    {:else if tab === "token"}
      <StreamTokens />
    {:else if tab === "security"}
      <Security />
    {/if}
  </div>
</SidebarProvider>
