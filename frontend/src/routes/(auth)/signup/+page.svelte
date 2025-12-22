<script lang="ts">
  import Button from "$lib/components/ui/button/button.svelte"
  import { server, validateUsername } from "$lib/utils.svelte"
  import Field, { submitButton } from "../../../lib/components/form.svelte"
  import { FieldGroup, FieldSet } from "$lib/components/ui/field"
  import { goto, invalidateAll } from "$app/navigation"
  import { resolve } from "$app/paths"

  let username = $state("")
  let password = $state("")
  let reenter = $state("")

  let invalidUsername = $state(false)
  let invalidPassword = $state(false)
  let invalidReenter = $state(false)
  let submit: Promise<void> | null = $state(null)
</script>

<div class="flex flex-col grow p-4">
  <div class="flex justify-end">
    <Button href="/login" variant="ghost">Log in</Button>
  </div>
  <div class="flex justify-center items-center grow">
    <form
      class="flex flex-col w-full max-w-sm gap-6"
      onsubmit={(event) => {
        event.preventDefault()
        submit = server.auth.signup(username, password, reenter).then(async () => {
          await invalidateAll()
          await goto(resolve("/"))
        })
      }}
    >
      <FieldSet>
        <h1 class="text-2xl font-semibold text-center">Create an account</h1>
        <FieldGroup>
          <Field
            id="username"
            label="Username"
            bind:value={username}
            debounce={300}
            validate={validateUsername}
            bind:invalid={invalidUsername}
            good="Username looks good!"
            description="Your unique user handle."
            validating="Checking username availability"
            autocomplete="username webauthn"
          />
          <Field
            id="password"
            label="Password"
            bind:value={password}
            type="password"
            validate={async (password: string) =>
              password.length >= 8 ? null : "Choose a password with at least 8 characters."}
            bind:invalid={invalidPassword}
            good="Password looks good!"
            autocomplete="new-password webauthn"
          />
          <Field
            id="reenter"
            label="Re-enter password"
            bind:value={reenter}
            type="password"
            validate={async (reenter: string) =>
              reenter === password ? null : "Ensure this matches your password above."}
            bind:invalid={invalidReenter}
            good="Passwords match!"
            autocomplete="new-password webauthn"
          />
          {@render submitButton(
            submit,
            !username || !password || invalidUsername || invalidPassword || invalidReenter,
          )}
        </FieldGroup>
      </FieldSet>
    </form>
  </div>
</div>
