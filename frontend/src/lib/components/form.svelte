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
  import type { Snippet } from "svelte"

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
    children,
    ...props
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
    children?: Snippet
    [key: string]: unknown
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
  next?: string,
  waiting?: string,
  done?: string,
)}
  {#if submit}
    {#await submit}
      <Button type="submit" disabled variant="secondary">
        <Spinner />
        {waiting ?? "Processing"}
      </Button>
    {:then}
      <Button type="submit" disabled variant="secondary">
        <Spinner />
        {done ?? "Redirecting"}
      </Button>
    {:catch}
      <Button type="submit" {disabled}>{next ?? "Continue"}</Button>
    {/await}
  {:else}
    <Button type="submit" {disabled}>{next ?? "Continue"}</Button>
  {/if}
{/snippet}

<Field data-invalid={invalid}>
  <FieldLabel for={id}>{label}</FieldLabel>
  <div class="flex gap-2">
    <Input {id} bind:value aria-invalid={invalid} {type} name={id} {autocomplete} {...props} />
    {@render children?.()}
  </div>
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
