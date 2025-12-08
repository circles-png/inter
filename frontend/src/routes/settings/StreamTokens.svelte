<script lang="ts">
  import { Field, FieldDescription, FieldLabel } from "$lib/components/ui/field"
  import {
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbList,
    BreadcrumbPage,
    BreadcrumbSeparator,
  } from "$lib/components/ui/breadcrumb"
  import Copy from "@lucide/svelte/icons/copy"
  import RotateCw from "@lucide/svelte/icons/rotate-cw"
  import {
    InputGroup,
    InputGroupAddon,
    InputGroupButton,
    InputGroupInput,
  } from "$lib/components/ui/input-group"
</script>

<div class="p-4 grow flex flex-col gap-2">
  <h1 class="text-2xl font-bold">Stream tokens</h1>
  <Field>
    <FieldLabel>Your token</FieldLabel>
    <InputGroup>
      <InputGroupInput type="password" disabled />
      <InputGroupAddon align="inline-end">
        <InputGroupButton>
          <Copy />
        </InputGroupButton>
      </InputGroupAddon>
      <InputGroupAddon align="inline-end">
        <InputGroupButton>
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
</div>

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
