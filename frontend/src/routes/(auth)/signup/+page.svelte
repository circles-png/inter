<script lang="ts">
  import { page } from "$app/state"
  import Button from "$lib/components/ui/button/button.svelte"
  import { getApiEndpoint } from "$lib/utils.svelte"
  import Field, { submitButton } from "../common.svelte"
  import { FieldGroup, FieldSet } from "$lib/components/ui/field"
  import { toast } from "svelte-sonner"

  let username = $state("")
  let password = $state("")
  let reenter = $state("")

  function debounce<A extends any[]>(f: (...args: A) => unknown, ms: number) {
    let timeout: number | null = null
    return (...args: A) => {
      if (timeout !== null) {
        window.clearTimeout(timeout)
      }
      timeout = window.setTimeout(() => f(...args), ms)
    }
  }

  function debounced<T>(get: () => T, ms: number) {
    let state = $state(get())
    const update = debounce((value) => {
      state = value
    }, ms)
    $effect(() => update(get()))
    return () => state
  }

  let debouncedUsername = debounced(() => username, 300)
  let usernameError = $derived.by(async () => {
    const username = debouncedUsername()
    if (!/^[a-z0-9_]*$/.test(username)) {
      return "Choose a username with only lowercase letters, numbers, and underscores."
    }
    if (username.length < 4) {
      return "Choose a username with at least 4 characters."
    }
    if (username.length > 32) {
      return "Choose a username with at most 32 characters."
    }
    const response = await fetch(
      getApiEndpoint(page.url.hostname, "http", `auth/available/${encodeURIComponent(username)}`),
      { method: "GET" },
    )
    if (response.status === 409) {
      return "Username is already taken."
    }
    return null
  })
  let invalidUsername = $state(false)
  let validPassword = $derived(password.length >= 8)
  let passwordsMatch = $derived(password === reenter)
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
        submit = fetch(getApiEndpoint(page.url.hostname, "http", "auth/signup"), {
          method: "POST",
          body: JSON.stringify({ username, password, reenter }),
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
        }).then(async (response) => {
          if (!response.ok) {
            const text = await response.text()
            toast.error("Error while signing up", {description: text})
            return Promise.reject(text)
          }
          location.replace("/")
          return Promise.resolve()
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
            error={usernameError}
            bind:invalid={invalidUsername}
            good="Username looks good!"
            description="Your unique user handle."
          />
          <Field
            id="password"
            label="Password"
            bind:value={password}
            type="password"
            error={!validPassword ? "Password must be at least 8 characters long" : null}
            good="Password looks good!"
          />
          <Field
            id="reenter"
            label="Re-enter password"
            bind:value={reenter}
            type="password"
            error={!passwordsMatch ? "Passwords do not match" : null}
            good="Passwords match!"
          />
          {@render submitButton(
            submit,
            !username || !password || !!invalidUsername || !validPassword || !passwordsMatch,
          )}
        </FieldGroup>
      </FieldSet>
    </form>
  </div>
</div>
