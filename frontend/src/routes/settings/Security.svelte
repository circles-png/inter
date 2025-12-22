<script>
  import { FieldGroup, FieldSet } from "$lib/components/ui/field"
  import Field, { submitButton } from "$lib/components/form.svelte"
  import { userUpdateContext } from "$lib/context.svelte"
  import { toast } from "svelte-sonner"
  import { server } from "$lib/utils.svelte"

  let previous = $state("")
  let next = $state("")
  let reenter = $state("")

  let invalidNext = $state(false)
  let invalidReenter = $state(false)
</script>

<form
  onsubmit={async (event) => {
    event.preventDefault()
    userUpdateContext.userUpdate = server.auth
      .updatePassword(previous, next, reenter)
      .then(async () => {
        previous = ""
        next = ""
        reenter = ""
        toast.success("Password updated")
        userUpdateContext.userUpdate = null
      })
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
