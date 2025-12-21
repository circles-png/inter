<script lang="ts">
  import {
    FieldGroup,
    FieldSet,
    Field as BaseField,
    FieldLabel,
    FieldDescription,
  } from "$lib/components/ui/field"
  import Field, { submitButton } from "$lib/components/form.svelte"
  import { goto } from "$app/navigation"
  import { colours, server, validateUsername } from "$lib/utils.svelte"
  import { toast } from "svelte-sonner"
  import { userContext, userUpdateContext } from "$lib/context.svelte"
  import { resolve } from "$app/paths"
  import type { User } from "../../models/user"
  import * as ImageCropper from "$lib/components/ui/image-cropper"
  import Separator from "$lib/components/ui/separator/separator.svelte"
  import { Popover, PopoverContent, PopoverTrigger } from "$lib/components/ui/popover"

  let initial: User | null = userContext.user
  if (initial === null) {
    goto(resolve("/login"))
    throw new Error("Redirecting to login")
  }
  let username = $state(initial.username)
  let displayName = $state(initial.displayName)
  let colour = $state(initial.colour)
  let invalidUsername = $state(false)
  let invalidDisplayName = $state(false)

  let src = $state<string | undefined>(initial.avatar || undefined)
</script>

<div class="p-4 grow flex flex-col gap-2">
  <h1 class="text-2xl font-bold">Profile</h1>
  <div class="flex gap-6">
    <BaseField class="w-auto">
      <FieldLabel>Profile picture</FieldLabel>
      <ImageCropper.Root
        bind:src
        onCropped={async (url) => {
          const user = userContext.user
          if (!user) return
          const file = await ImageCropper.getFileFromUrl(url)
          if (file.size > 16 * 1024 * 1024) {
            toast.error("Error while updating profile picture", {
              description: "Choose a file smaller than 16 MiB.",
            })
            src = user.avatar || undefined
            return
          }
          userUpdateContext.userUpdate = server.auth.updateAvatar(file)
          await userUpdateContext.userUpdate
          src = (await server.auth.user()).avatar || undefined
          toast.success("Account updated")
          location.reload()
        }}
      >
        <ImageCropper.UploadTrigger>
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
    <Separator orientation="vertical" />
    <form
      onsubmit={async (event) => {
        event.preventDefault()
        const user = userContext.user
        if (!user) return
        userContext.user = { ...user, username: username, displayName: displayName, colour: colour }
        await userUpdateContext.userUpdate
        toast.success("Account updated")
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
              if (!initial) return undefined
              if (username == initial.username) return undefined
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
              if (!initial) return undefined
              if (displayName == initial.displayName) return undefined
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
            userUpdateContext.userUpdate,
            !username || invalidUsername || invalidDisplayName,
            "Update",
          )}
        </FieldGroup>
      </FieldSet>
    </form>
  </div>
</div>
