<script lang="ts">
  import {
    FieldGroup,
    FieldSet,
    Field as BaseField,
    FieldLabel,
    FieldDescription,
  } from "$lib/components/ui/field"
  import Field, { submitButton } from "$lib/components/form.svelte"
  import { invalidateAll } from "$app/navigation"
  import { colours, server, validateUsername } from "$lib/utils.svelte"
  import { toast } from "svelte-sonner"
  import * as ImageCropper from "$lib/components/ui/image-cropper"
  import Separator from "$lib/components/ui/separator/separator.svelte"
  import { Popover, PopoverContent, PopoverTrigger } from "$lib/components/ui/popover"
  import type { User } from "../../models/user"
  import { IsMobile } from "$lib/hooks/is-mobile.svelte"
  import { InputGroupAddon, InputGroupText } from "$lib/components/ui/input-group"

  let { user }: { user: User } = $props()
  // svelte-ignore state_referenced_locally
  let next = $state({
    next: {
      username: user.username,
      displayName: user.displayName,
      colour: user.colour,
      src: server.user.avatar(user.username),
    },
  })
  let { username, displayName, colour, src } = $derived(next.next)
  let invalidUsername = $state(false)
  let invalidDisplayName = $state(false)
  let update: Promise<void> | null = $state(null)
  let isMobile = new IsMobile()
  let upload: HTMLLabelElement | null = $state(null)
</script>

<div class="flex gap-6 flex-col md:flex-row">
  <BaseField class="w-auto">
    <FieldLabel for={upload?.htmlFor}>Profile picture</FieldLabel>
    <ImageCropper.Root
      bind:src
      onCropped={async (url) => {
        const file = await ImageCropper.getFileFromUrl(url)
        if (file.size > 16 * 1024 * 1024) {
          toast.error("Error while updating profile picture", {
            description: "Choose a file smaller than 16 MiB.",
          })
          src = server.user.avatar(user.username)
          return
        }
        await server.auth.updateAvatar(file)
        await invalidateAll()
        next.next = {
          username: user.username,
          displayName: user.displayName,
          colour: user.colour,
          src: server.user.avatar(user.username),
        }
        toast.success("Account updated")
        location.reload()
      }}
    >
      <ImageCropper.UploadTrigger bind:ref={upload}>
        <ImageCropper.Preview />
      </ImageCropper.UploadTrigger>
      <ImageCropper.Dialog>
        <ImageCropper.Cropper />
        <ImageCropper.Controls>
          <ImageCropper.Crop />
          <ImageCropper.Cancel />
        </ImageCropper.Controls>
      </ImageCropper.Dialog>
    </ImageCropper.Root>
    <FieldDescription>Maximum size is 16 MiB.</FieldDescription>
  </BaseField>
  <Separator orientation={isMobile.current ? "horizontal" : "vertical"} />
  <form
    onsubmit={async (event) => {
      event.preventDefault()
      update = server.auth.update({ username: username, displayName: displayName, colour: colour })
      await invalidateAll()
      toast.success("Account updated")
      update = null
    }}
    class="grow"
  >
    <FieldSet class="max-w-lg">
      <FieldGroup>
        <Field
          id="username"
          label="Username"
          bind:value={username}
          debounce={300}
          validate={async (username) => {
            if (username == user.username) return undefined
            return await validateUsername(username)
          }}
          bind:invalid={invalidUsername}
          good="Username looks good!"
          description="This is your unique user handle."
          validating="Checking username availability"
          autocomplete="username webauthn"
          class="transition-colors duration-300"
          style={`color: ${colours[colour]}`}
        >
          {#snippet group()}
            <InputGroupAddon><InputGroupText>@</InputGroupText></InputGroupAddon>
          {/snippet}
          <Popover>
            <PopoverTrigger class="p-1 size-9" title="Choose colour">
              <div
                class="size-7 border rounded-full transition-all duration-300 hover:brightness-110 hover:scale-105"
                style:background-color={colours[colour]}
              ></div>
            </PopoverTrigger>
            <PopoverContent class="w-auto" align="end">
              <div class="grid grid-cols-5 gap-2">
                {#each colours as current, index (current)}
                  <button
                    style:background-color={current}
                    class="size-7 border rounded-full hover:brightness-110 transition hover:scale-105"
                    title={current}
                    onclick={() => (colour = index)}
                  ></button>
                {/each}
              </div>
            </PopoverContent>
          </Popover>
        </Field>
        <Field
          id="display-name"
          label="Display name"
          bind:value={displayName}
          validate={async (displayName) => {
            if (displayName == user.displayName) return undefined
            if (new TextEncoder().encode(displayName).byteLength > 32) {
              return "Choose a shorter display name."
            }
            return null
          }}
          bind:invalid={invalidDisplayName}
          good="Display name looks good!"
          description="This is your public display name."
          autocomplete="name"
        />
        {@render submitButton(
          update,
          !username || invalidUsername || invalidDisplayName,
          "Update",
          "Processing",
          "Processing",
        )}
      </FieldGroup>
    </FieldSet>
  </form>
</div>
