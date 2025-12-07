<script lang="ts">
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
  import {
    Field,
    FieldDescription,
    FieldGroup,
    FieldLabel,
    FieldSet,
  } from "$lib/components/ui/field"
  import { Input } from "$lib/components/ui/input"
  import {
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbList,
    BreadcrumbPage,
    BreadcrumbSeparator,
  } from "$lib/components/ui/breadcrumb"
  import Copy from "@lucide/svelte/icons/copy"
  import RotateCw from "@lucide/svelte/icons/rotate-cw"
  import {
    InputGroup,
    InputGroupAddon,
    InputGroupButton,
    InputGroupInput,
  } from "$lib/components/ui/input-group"

</script>

<div class="p-4 grow flex flex-col gap-2">
  <h1 class="text-2xl font-bold">Stream tokens</h1>
  <Field>
    <FieldLabel>Your token</FieldLabel>
    <InputGroup>
      <InputGroupInput type="password" disabled/>
      <InputGroupAddon align="inline-end">
        <InputGroupButton>
          <Copy />
        </InputGroupButton>
      </InputGroupAddon>
      <InputGroupAddon align="inline-end">
        <InputGroupButton>
          <RotateCw />
          Rotate
        </InputGroupButton>
      </InputGroupAddon>
    </InputGroup>
    <FieldDescription>
      This is your stream token used for authentication. Keep it secret. In OBS Studio's {@render two(
        "Settings",
        "Stream",
      )}, select {@render two("Service", "WHIP")} and enter the token in {@render two(
        "Destination",
        "Bearer Token",
      )}.
    </FieldDescription>
  </Field>
</div>

{#snippet two(a: string, b: string)}
  <Breadcrumb class="inline-block">
    <BreadcrumbList class="gap-0.5!">
      <BreadcrumbItem>
        <BreadcrumbPage>{a}</BreadcrumbPage>
      </BreadcrumbItem>
      <BreadcrumbSeparator />
      <BreadcrumbItem>
        <BreadcrumbPage>{b}</BreadcrumbPage>
      </BreadcrumbItem>
    </BreadcrumbList>
  </Breadcrumb>
{/snippet}
