<script lang="ts">
  import { page } from "$app/state"
  import Button from "$lib/components/ui/button/button.svelte"
  import { getApiEndpoint } from "$lib/utils.svelte"
  import Field, { submitButton } from "../common.svelte"
  import { FieldGroup, FieldSet } from "$lib/components/ui/field"
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
        submit = fetch(getApiEndpoint(page.url.hostname, "http", "auth/login"), {
          method: "POST",
          body: JSON.stringify({ username, password }),
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
        }).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            return Promise.reject(text)
          }
          location.replace("/")
          return Promise.resolve()
        })
      }}
    >
      <FieldSet>
        <h1 class="text-2xl font-semibold text-center">Log in to your existing account</h1>
        <FieldGroup>
          <Field id="username" label="Username" bind:value={username} />
          <Field id="password" label="Password" bind:value={password} type="password" />
          {@render submitButton(submit, !username || !password)}
        </FieldGroup>
      </FieldSet>
    </form>
  </div>
</div>
