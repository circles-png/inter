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
  import { debounced } from "$lib/utils.svelte"
  import type { FullAutoFill } from "svelte/elements"

  let {
    id,
    label,
    value = $bindable(),
    type = "text",
    debounce = 0,
    validate,
    invalid = $bindable(false),
    good,
    description,
    validating,
    autocomplete,
  }: {
    id: string
    label: string
    value: string
    type?: string
    debounce?: number
    validate?: (value: string) => Promise<string | null | undefined>
    invalid?: boolean
    good?: string
    description?: string
    validating?: string
    autocomplete?: FullAutoFill
  } = $props()
  const debouncedValue = debounced(() => value, debounce)
  const error = $derived(validate?.(debouncedValue()) || Promise.resolve(undefined))
  let unchanged = $state(true)
  $effect(() => {
    error.then((error) => {
      invalid = !!value && !!error
      unchanged = error === undefined
    })
  })
</script>

{#snippet submitButton(
  submit: Promise<void> | null,
  disabled: boolean,
  next: string = "Continue",
  waiting: string = "Processing",
  done: string = "Redirecting",
)}
  {#snippet submitButtonInner(disabled: boolean)}
    <Button type="submit" {disabled}>{next}</Button>
  {/snippet}

  {#if submit}
    {#await submit}
      <Button type="submit" disabled variant="secondary">
        <Spinner />
        {waiting}
      </Button>
    {:then}
      <Button type="submit" disabled variant="secondary">
        <Spinner />
        {done}
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
  <Input {id} bind:value aria-invalid={invalid} {type} name={id} {autocomplete} />
  {#if value && error !== undefined && !unchanged}
    {#await error}
      <p class="text-sm text-muted-foreground flex gap-1">
        <Spinner />
        {validating}
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

{#snippet errorDisplay(error: string | null | undefined)}
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
