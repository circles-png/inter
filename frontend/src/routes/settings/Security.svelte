<script>
  import { FieldGroup, FieldLabel, FieldSet } from "$lib/components/ui/field"
  import Field, { submitButton } from "$lib/components/form.svelte"
  import { userContext, userUpdateContext } from "$lib/context.svelte"
  import { toast } from "svelte-sonner"
  import { getApiEndpoint } from "$lib/utils.svelte"

  let previous = $state("")
  let next = $state("")
  let reenter = $state("")

  let invalidNext = $state(false)
  let invalidReenter = $state(false)
</script>

<div class="p-4 grow flex flex-col gap-2">
  <h1 class="text-2xl font-bold">Security</h1>
  <form
    onsubmit={async (event) => {
      event.preventDefault()
      userUpdateContext.userUpdate = fetch(getApiEndpoint("http", "auth/update/password"), {
        method: "POST",
        body: JSON.stringify({
          currentPassword: previous,
          newPassword: next,
          reenterPassword: reenter,
        }),
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
      }).then(async (response) => {
        if (!response.ok) {
          const text = await response.text()
          toast.error("Error while updating password", { description: text })
          return Promise.reject(text)
        }
         previous = ""
        next = ""
        reenter = ""
        toast.success("Password updated")
      })
      await userUpdateContext.userUpdate
      userUpdateContext.userUpdate = null
    }}
  >
    <FieldSet>
      <FieldGroup class="max-w-lg">
        <Field
          id="password"
          label="Current password"
          bind:value={previous}
          type="password"
          autocomplete="current-password webauthn"
        />
        <Field
          id="next"
          label="New password"
          bind:value={next}
          validate={async (password) => {
            if (password.length < 8) {
              return "Choose a password with at least 8 characters."
            }
            return null
          }}
          good="Password looks good!"
          type="password"
          bind:invalid={invalidNext}
          autocomplete="new-password webauthn"
        />
        <Field
          id="reenter"
          label="Re-enter new password"
          bind:value={reenter}
          validate={async (password) => {
            if (password !== next) {
              return "Ensure this matches your new password above."
            }
            return null
          }}
          good="Passwords match!"
          type="password"
          bind:invalid={invalidReenter}
          autocomplete="new-password webauthn"
        />
        {@render submitButton(
          userUpdateContext.userUpdate,
          !previous || !next || !reenter || invalidNext || invalidReenter,
          "Update",
        )}
      </FieldGroup>
    </FieldSet>
  </form>
</div>
