<script lang="ts">
  import { Button } from "$lib/components/ui/button"
  import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
  } from "$lib/components/ui/sheet"
  import "../app.css"
  import ProfileMenu from "./ProfileMenu.svelte"
  import Menu from "@lucide/svelte/icons/menu"

  interface Props {
    user?: User
    onLogin?: () => void
    onLogout?: () => void
    onCreateAccount?: () => void
  }

  const { user, onLogin, onLogout, onCreateAccount: onSignUp }: Props = $props()
  let menuOpen = $state(false)
</script>

<header
  class="border-r lg:border-b lg:border-r-0 flex flex-col lg:flex-row items-center p-4 justify-between [*:has(&)]:h-full h-full basis-0"
>
  <div class="size-8 flex justify-end items-end bg-white rounded-md"></div>
  <div class="flex flex-col items-center gap-2 lg:hidden">
    {#if user}
      <ProfileMenu {user} {onLogout} />
    {:else}
      <Sheet>
        <SheetTrigger>
          <Button onclick={() => (menuOpen = !menuOpen)} size="icon" variant="secondary">
            <Menu />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" class="flex flex-col gap-2 justify-end">
          <Button variant="secondary" href="/login">Log in</Button>
          <Button href="/signup">Sign up</Button>
        </SheetContent>
      </Sheet>
    {/if}
  </div>
  <div class="items-center gap-2 hidden lg:flex">
    {#if user}
      <ProfileMenu {user} {onLogout} />
    {:else}
      <Button variant="secondary" href="/login">Log in</Button>
      <Button href="/signup">Sign up</Button>
    {/if}
  </div>
</header>
