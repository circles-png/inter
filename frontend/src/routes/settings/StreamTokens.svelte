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
  import Eye from "@lucide/svelte/icons/eye"
  import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
  } from "$lib/components/ui/dialog"
  import { Button, buttonVariants } from "$lib/components/ui/button"

  let { user }: { user: User } = $props()
  let showToken = $state(false)
  const token = $derived(user.streamToken)
</script>

<Field>
  <FieldLabel>Your token</FieldLabel>
  <InputGroup>
    <InputGroupInput
      disabled
      readonly
      type={showToken ? "text" : "password"}
      value={token}
      class="overflow-scroll"
    />
    <InputGroupAddon align="inline-end">
      <Dialog>
        <DialogTrigger>
          <InputGroupButton>
            <Eye />
            View
          </InputGroupButton>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Are you sure you want to view your stream token?</DialogTitle>
            <DialogDescription>
              This will reveal your stream token. Rotate it if you believe it has been compromised.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="destructive" onclick={() => (showToken = true)}>Reveal</Button>
            <DialogClose class={buttonVariants({ variant: "default" })}>Cancel</DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </InputGroupAddon>
    <InputGroupAddon align="inline-end">
      <InputGroupButton>
        {#snippet child({ props })}
          <CopyButton text={token} {...props}>Copy</CopyButton>
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
