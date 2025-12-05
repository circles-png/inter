<script lang="ts">
  import X from "@lucide/svelte/icons/x"
  import { Input } from "./ui/input"
  import { Label } from "./ui/label"
  import Check from "@lucide/svelte/icons/check"
  import Spinner from "./ui/spinner/spinner.svelte"
  import { Field, FieldDescription, FieldError, FieldLabel } from "./ui/field"

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
    error: (string | null) | Promise<string | null>
    invalid?: boolean
    good: string
    description?: string
  } = $props()
  const error = $derived(
    errorPromise instanceof Promise ? errorPromise : Promise.resolve(errorPromise),
  )
  $effect(() => {
    invalid = !!value
    error.then((error) => (invalid = !!value && !!error))
  })
</script>

<Field data-invalid={invalid}>
  <FieldLabel for={id}>{label}</FieldLabel>
  <Input {id} bind:value aria-invalid={invalid} {type} name={id} />
  {#if value}
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
