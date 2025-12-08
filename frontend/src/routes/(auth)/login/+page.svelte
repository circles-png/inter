<script lang="ts">
  import Button from "$lib/components/ui/button/button.svelte"
  import { getApiEndpoint } from "$lib/utils.svelte"
  import Field, { submitButton } from "../../../lib/components/form.svelte"
  import { FieldGroup, FieldSet } from "$lib/components/ui/field"
  import { toast } from "svelte-sonner"
  import { goto } from "$app/navigation"
  import { loadUser } from "../../+layout.svelte"
  import { resolve } from "$app/paths"
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
        submit = fetch(getApiEndpoint("http", "auth/login"), {
          method: "POST",
          body: JSON.stringify({ username, password }),
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
        }).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            toast.error("Error while logging in", { description: text })
            return Promise.reject(text)
          }
          await goto(resolve("/"))
          loadUser()
        })
      }}
    >
      <FieldSet>
        <h1 class="text-2xl font-semibold text-center">Log in to your existing account</h1>
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
