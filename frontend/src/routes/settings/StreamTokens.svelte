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
  import { userContext } from "$lib/context.svelte"
  import { CopyButton } from "$lib/components/ui/copy-button"
  import { getApiEndpoint } from "$lib/utils.svelte"
  import { toast } from "svelte-sonner"
  import { goto } from "$app/navigation"
  import { resolve } from "$app/paths"

  let token = {
    async get() {
      const user = await userContext.user
      if (!user) {
        await goto(resolve("/login"))
        return ""
      }
      return user.streamToken
    },
    async set(newToken: string) {
      const user = await userContext.user
      if (!user) {
        await goto(resolve("/login"))
        return ""
      }
      userContext.user = Promise.resolve({ ...user, streamToken: newToken })
    },
  }
</script>

<div class="p-4 grow flex flex-col gap-2">
  <h1 class="text-2xl font-bold">Stream tokens</h1>
  <Field>
    <FieldLabel>Your token</FieldLabel>
    <InputGroup>
      <InputGroupInput disabled value={await token.get()} />
      <InputGroupAddon align="inline-end">
        <InputGroupButton>
          {#snippet child({ props })}
            <CopyButton text={await token.get()} {...props}>Copy</CopyButton>
          {/snippet}
        </InputGroupButton>
      </InputGroupAddon>
      <InputGroupAddon align="inline-end">
        <InputGroupButton
          onclick={async () => {
            const response = await fetch(getApiEndpoint("http", "stream-token"))
            token.set(await response.text())
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
