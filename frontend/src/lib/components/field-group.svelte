<script lang="ts">
  import X from "@lucide/svelte/icons/x"
  import { Input } from "./ui/input"
  import { Label } from "./ui/label"
  import Check from "@lucide/svelte/icons/check"
  import Spinner from "./ui/spinner/spinner.svelte"

  let {
    id,
    label,
    value = $bindable(),
    type = "text",
    error,
    good,
  }: {
    id: string
    label: string
    value: string
    type?: string
    error: (string | null) | Promise<string | null>
    good: string
  } = $props()
</script>

<div class="flex flex-col gap-2">
  <Label for={id}>{label}</Label>
  <div class="flex flex-col">
    {#if error instanceof Promise}
      {#await error}
        {@render input()}
      {:then error}
        {@render input(!!error)}
      {/await}
    {:else}
      {@render input(!!error)}
    {/if}
    {#if value}
      {#if error instanceof Promise}
        {#await error}
          <p class="text-sm text-muted-foreground flex gap-1">
            <Spinner />
            Checking username availability
          </p>
        {:then error}
          {@render errorDisplay(error)}
        {/await}
      {:else}
        {@render errorDisplay(error)}
      {/if}
    {/if}
  </div>
</div>

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

{#snippet input(extraCondition: boolean = true)}
  <Input {id} bind:value aria-invalid={!!value && extraCondition} {type} name={id} />
{/snippet}
