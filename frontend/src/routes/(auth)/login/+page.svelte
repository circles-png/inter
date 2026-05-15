<script lang="ts">
  import Button from "$lib/components/ui/button/button.svelte"
  import Field, { submitButton } from "../../../lib/components/form.svelte"
  import { FieldGroup, FieldSet } from "$lib/components/ui/field"
  import { goto, invalidateAll } from "$app/navigation"
  import { resolve } from "$app/paths"
  import { server } from "$lib/utils.svelte"
  import Logo from "$lib/components/logo.svelte"
  let username = $state("")
  let password = $state("")
  let submit: Promise<void> | null = $state(null)
</script>

<div class="flex flex-col grow p-4">
  <div class="flex justify-end">
    <Button href="/signup" variant="ghost">Sign up</Button>
  </div>
  <div class="flex justify-center items-center grow">
    <form
      class="flex flex-col w-full max-w-sm gap-6"
      onsubmit={(event) => {
        event.preventDefault()
        submit = server.auth.login(username, password).then(async () => {
          await invalidateAll()
          await goto(resolve("/"))
        })
      }}
    >
      <FieldSet>
        <h1
          class="text-2xl font-semibold text-center flex gap-2 items-center justify-center [&_svg]:h-11"
        >
          Log in to <Logo wordmark />
        </h1>
        <FieldGroup>
          <Field
            id="username"
            label="Username"
            bind:value={username}
            autocomplete="username webauthn"
          />
          <Field
            id="password"
            label="Password"
            bind:value={password}
            type="password"
            autocomplete="current-password webauthn"
          />
          {@render submitButton(submit, !username || !password)}
        </FieldGroup>
      </FieldSet>
    </form>
  </div>
</div>
