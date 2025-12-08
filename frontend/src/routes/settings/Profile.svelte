<script lang="ts">
  import { FieldGroup, FieldSet } from "$lib/components/ui/field"
  import Field, { submitButton } from "$lib/components/form.svelte"
  import { goto } from "$app/navigation"
  import { validateUsername } from "$lib/utils.svelte"
  import { toast } from "svelte-sonner"
  import { userContext, userUpdateContext } from "$lib/context.svelte"
  import { resolve } from "$app/paths"
  import type { User } from "../../models/user"

  let initial: User | null = null
  let username = $state("")
  let displayName = $state("")
  let invalidUsername = $state(false)
  let invalidDisplayName = $state(false)

  userContext.user.then(async (user) => {
    if (user === null) {
      await goto(resolve("/login"))
      return
    }
    initial = user
    username = user.username
    displayName = user.displayName
  })
</script>

<div class="p-4 grow flex flex-col gap-2">
  <h1 class="text-2xl font-bold">Profile</h1>
  <form
    onsubmit={async (event) => {
      event.preventDefault()
      const user = await userContext.user
      if (!user) return
      userContext.user = Promise.resolve({ ...user, username, displayName })
      await userUpdateContext.userUpdate
      userUpdateContext.userUpdate = null
      toast.success("Account updated")
    }}
  >
    <FieldSet>
      <FieldGroup class="max-w-lg">
        <Field
          id="username"
          label="Username"
          bind:value={username}
          debounce={300}
          validate={async (username) => {
            if (!initial) return undefined
            if (username == initial.username) return undefined
            return await validateUsername(username)
          }}
          bind:invalid={invalidUsername}
          good="Username looks good!"
          description="This is your unique user handle."
          validating="Checking username availability"
          autocomplete="username webauthn"
        />
        <Field
          id="display-name"
          label="Display name"
          bind:value={displayName}
          validate={async (displayName) => {
            if (!initial) return undefined
            if (displayName == initial.displayName) return undefined
            if (new TextEncoder().encode(displayName).byteLength > 32) {
              return "Choose a shorter display name."
            }
            return null
          }}
          bind:invalid={invalidDisplayName}
          good="Display name looks good!"
          description="This is your public display name."
          autocomplete="name"
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
