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

  let password = $state("")
</script>

<div class="p-4 grow flex flex-col gap-2">
  <h1 class="text-2xl font-bold">Security</h1>
  <form
    onsubmit={async (event) => {
      event.preventDefault()
      userContext.user = Promise.resolve({ ...user, username, displayName })
      await userUpdateContext.userUpdate
      userUpdateContext.userUpdate = null
    }}
  >
    <FieldSet>
      <FieldGroup class="max-w-lg">
        <Field
          id="password"
          label="Username"
          bind:value={password}
          debounce={300}
          validate={async (username) => {
            if (username == user.username) return undefined
            return await validateUsername(username)
          }}
          bind:invalid={invalidUsername}
          good="Username looks good!"
          description="This is your unique user handle."
          validating="Checking username availability"
          autocomplete="username webauthn"
        />
        {@render submitButton(
          userUpdateContext.userUpdate,
          !username || invalidUsername || invalidDisplayName,
          "Update",
        )}
      </FieldGroup>
    </FieldSet>
  </form>
</div>
