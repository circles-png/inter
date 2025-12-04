<script lang="ts">
  import { Avatar } from "$lib/components/ui/avatar"
  import AvatarFallback from "$lib/components/ui/avatar/avatar-fallback.svelte"
  import AvatarImage from "$lib/components/ui/avatar/avatar-image.svelte"
  import Button from "$lib/components/ui/button/button.svelte"
  import {
    Sheet,
    SheetTrigger,
    SheetContent,
    SheetHeader,
    SheetTitle,
  } from "$lib/components/ui/sheet"
  import "../app.css"

  interface Props {
    user: User
    onLogout?: () => void
  }

  const { user, onLogout }: Props = $props()
</script>

<Sheet>
  <SheetTrigger>
    <button>
      <Avatar>
        <AvatarImage src={user.avatar} alt={user.username} />
        <AvatarFallback class="bg-muted" />
      </Avatar>
    </button>
  </SheetTrigger>
  <SheetContent side="left">
    <SheetHeader>
      <SheetTitle>Profile</SheetTitle>
    </SheetHeader>
    <div class="flex flex-col justify-between grow p-4 pt-0">
      <div class="">hi</div>
      <Button onclick={onLogout}>Log out</Button>
    </div>
  </SheetContent>
</Sheet>
