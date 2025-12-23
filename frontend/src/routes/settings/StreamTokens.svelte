<script lang="ts">
  import { Field, FieldDescription, FieldLabel } from "$lib/components/ui/field"
  import {
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbList,
    BreadcrumbPage,
    BreadcrumbSeparator,
  } from "$lib/components/ui/breadcrumb"
  import RotateCw from "@lucide/svelte/icons/rotate-cw"
  import {
    InputGroup,
    InputGroupAddon,
    InputGroupButton,
    InputGroupInput,
  } from "$lib/components/ui/input-group"
  import { CopyButton } from "$lib/components/ui/copy-button"
  import { toast } from "svelte-sonner"
  import { server } from "$lib/utils.svelte"
  import { invalidateAll } from "$app/navigation"
  import type { User } from "../../models/user"

  let { user }: { user: User } = $props()
  const token = $derived(user.streamToken)
</script>

<Field>
  <FieldLabel>Your token</FieldLabel>
  <InputGroup>
    <InputGroupInput disabled value={await token} class="overflow-scroll" />
    <InputGroupAddon align="inline-end">
      <InputGroupButton>
        {#snippet child({ props })}
          <CopyButton text={await token} {...props}>Copy</CopyButton>
        {/snippet}
      </InputGroupButton>
    </InputGroupAddon>
    <InputGroupAddon align="inline-end">
      <InputGroupButton
        onclick={async () => {
          await server.auth.updateStreamToken()
          await invalidateAll()
          toast.success("Stream token rotated")
        }}
      >
        <RotateCw />
        Rotate
      </InputGroupButton>
    </InputGroupAddon>
  </InputGroup>
  <FieldDescription>
    This is your stream token used for authentication. Keep it secret. In OBS Studio's {@render two(
      "Settings",
      "Stream",
    )}, select {@render two("Service", "WHIP")} and enter the token in {@render two(
      "Destination",
      "Bearer Token",
    )}.
  </FieldDescription>
</Field>

{#snippet two(a: string, b: string)}
  <Breadcrumb class="inline-block">
    <BreadcrumbList class="gap-0.5!">
      <BreadcrumbItem>
        <BreadcrumbPage>{a}</BreadcrumbPage>
      </BreadcrumbItem>
      <BreadcrumbSeparator />
      <BreadcrumbItem>
        <BreadcrumbPage>{b}</BreadcrumbPage>
      </BreadcrumbItem>
    </BreadcrumbList>
  </Breadcrumb>
{/snippet}
