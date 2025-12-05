<script module>
  export { submitButton }
</script>

<script lang="ts">
  import X from "@lucide/svelte/icons/x"
  import Check from "@lucide/svelte/icons/check"
  import { Field, FieldLabel, FieldError, FieldDescription } from "$lib/components/ui/field"
  import { Input } from "$lib/components/ui/input"
  import { Spinner } from "$lib/components/ui/spinner"
  import { Button } from "$lib/components/ui/button"

  let {
    id,
    label,
    value = $bindable(),
    type = "text",
    error: errorPromise,
    invalid = $bindable(false),
    good,
    description,
  }: {
    id: string
    label: string
    value: string
    type?: string
    error?: (string | null) | Promise<string | null>
    invalid?: boolean
    good?: string
    description?: string
  } = $props()
  const error = $derived(
    errorPromise !== undefined
      ? errorPromise instanceof Promise
        ? errorPromise
        : Promise.resolve(errorPromise)
      : Promise.resolve(null),
  )
  $effect(() => {
    invalid = !!value
    error.then((error) => (invalid = !!value && !!error))
  })
</script>

{#snippet submitButton(submit: Promise<void> | null, disabled: boolean)}
  {#snippet submitButtonInner(disabled: boolean)}
    <Button type="submit" {disabled}>Continue</Button>
  {/snippet}

  {#if submit}
    {#await submit}
      <Button type="submit" disabled variant="secondary">
        <Spinner />
        Processing
      </Button>
    {:then}
      <Button type="submit" disabled variant="secondary">
        <Spinner />
        Redirecting
      </Button>
    {:catch}
      {@render submitButtonInner(disabled)}
    {/await}
  {:else}
    {@render submitButtonInner(disabled)}
  {/if}
{/snippet}

<Field data-invalid={invalid}>
  <FieldLabel for={id}>{label}</FieldLabel>
  <Input {id} bind:value aria-invalid={invalid} {type} name={id} />
  {#if value && errorPromise !== undefined}
    {#await error}
      <p class="text-sm text-muted-foreground flex gap-1">
        <Spinner />
        Checking username availability
      </p>
    {:then error}
      <FieldError>
        {@render errorDisplay(error)}
      </FieldError>
    {/await}
  {/if}
  {#if description}
    <FieldDescription>{description}</FieldDescription>
  {/if}
</Field>

{#snippet errorDisplay(error: string | null)}
  {#if error}
    <p class="text-sm text-destructive flex gap-1">
      <X class="size-5" />
      {error}
    </p>
  {:else}
    <p class="text-sm text-green-400 flex gap-1">
      <Check class="size-5" />
      {good}
    </p>
  {/if}
{/snippet}
