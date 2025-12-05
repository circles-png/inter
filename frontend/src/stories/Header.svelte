<script lang="ts">
  import Logo from "$lib/components/logo.svelte"
  import { Avatar, AvatarFallback, AvatarImage } from "$lib/components/ui/avatar"
  import { Button } from "$lib/components/ui/button"
  import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
  } from "$lib/components/ui/sheet"
  import { cn } from "$lib/utils"
  import { Tween } from "svelte/motion"
  import "../app.css"
  import type { User } from "../models/user"
  import ProfileMenu from "./ProfileMenu.svelte"
  import Menu from "@lucide/svelte/icons/menu"
  import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarProvider,
    SidebarTrigger,
  } from "$lib/components/ui/sidebar"

  interface Props {
    user?: User
    onLogin?: () => void
    onLogout?: () => void
    onCreateAccount?: () => void
  }

  const { user, onLogin, onLogout, onCreateAccount: onSignUp }: Props = $props()
  let menuWidth = new Tween(0, {
    easing(t) {
      return 1 - Math.pow(1 - t, 5)
    },
  })
</script>

<SidebarProvider>
  <Sidebar collapsible="icon" variant="floating">
    <SidebarContent>
      <SidebarGroup>
        <SidebarGroupLabel></SidebarGroupLabel>
        <SidebarGroupContent></SidebarGroupContent>
      </SidebarGroup>

      <header class="flex p-2 w-16">
        <div class="flex p-2 bg-sidebar rounded-lg border border-border gap-4">
          <div class="flex flex-col lg:flex-row items-center justify-between">
            <Logo />
            <div class="flex flex-col items-center gap-2 lg:hidden">
              {#if user}
                <ProfileMenu {user} {onLogout} />
              {:else}
                <Button
                  onclick={() => menuWidth.set(menuWidth.target === 0 ? 56 : 0)}
                  size="icon"
                  variant="secondary"
                >
                  <Menu />
                </Button>
              {/if}
            </div>
            <div class="items-center gap-2 hidden lg:flex">
              {#if user}
                <Avatar>
                  <AvatarImage src={user.avatar} alt={user.username} />
                  <AvatarFallback class="bg-muted" />
                </Avatar>
              {:else}
                <Button variant="secondary" href="/login">Log in</Button>
                <Button href="/signup">Sign up</Button>
              {/if}
            </div>
          </div>
          <div class={cn("flex flex-col justify-between")} style="width: {menuWidth.current}px;">
            <div class=""></div>
            {#if user}
              <ProfileMenu {user} {onLogout} />
            {:else}
              <div class="flex gap-2">
                <Button variant="secondary" href="/login">Log in</Button>
                <Button href="/signup">Sign up</Button>
              </div>
            {/if}
          </div>
        </div>
      </header>
    </SidebarContent>
  </Sidebar>
  <SidebarFooter />

  <SidebarTrigger />
</SidebarProvider>
