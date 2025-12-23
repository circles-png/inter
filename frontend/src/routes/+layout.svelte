<script lang="ts">
  import { Toaster } from "$lib/components/ui/sonner"
  import CircleAlert from "@lucide/svelte/icons/circle-alert"
  import "../app.css"
  const { children } = $props()
</script>

<Toaster richColors closeButton>
  {#snippet errorIcon()}
    <CircleAlert class="size-5" />
  {/snippet}
</Toaster>

{@render children()}
