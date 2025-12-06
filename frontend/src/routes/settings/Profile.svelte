<script lang="ts">
  import { FieldGroup, FieldSet } from "$lib/components/ui/field"
  import Field, { submitButton } from "$lib/components/form.svelte"
  import { goto } from "$app/navigation"
  import { getApiEndpoint, validateUsername } from "$lib/utils.svelte"
  import { toast } from "svelte-sonner"
  import { userContext, userUpdateContext } from "$lib/context.svelte"

  const user = await userContext.user
  if (user === null) {
    goto("/login")
    throw new Error("Redirecting to login")
  }
  let username = $state(user.username)
  let displayName = $state(user.displayName ?? "")
  let invalidUsername = $state(false)
  let invalidDisplayName = $state(false)
</script>

<div class="p-4 grow flex flex-col gap-2">
  <h1 class="text-2xl font-bold">Profile</h1>
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
          id="username"
          label="Username"
          bind:value={username}
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
        <Field
          id="display-name"
          label="Display name"
          bind:value={displayName}
          validate={async (displayName) => {
            if (displayName == user.displayName) return undefined
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
