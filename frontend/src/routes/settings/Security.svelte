<script>
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
  import Settings from "@lucide/svelte/icons/settings"
  import CircleUser from "@lucide/svelte/icons/circle-user"
  import KeyRound from "@lucide/svelte/icons/key-round"
  import Lock from "@lucide/svelte/icons/lock"
  import { FieldGroup, FieldLabel, FieldSet } from "$lib/components/ui/field"
  import Field from "$lib/components/form.svelte"

  let tab = $state("profile")
</script>

<div class="p-4 grow flex flex-col gap-2">
  <h1 class="text-2xl font-bold">Security</h1>
</div>
