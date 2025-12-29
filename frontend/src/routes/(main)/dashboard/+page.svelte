<script lang="ts">
  import { invalidateAll } from "$app/navigation"
  import { Button, buttonVariants } from "$lib/components/ui/button"
  import { ButtonGroup } from "$lib/components/ui/button-group"
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
  import { Field, FieldGroup, FieldLabel, FieldSet } from "$lib/components/ui/field"
  import { Input } from "$lib/components/ui/input"
  import { cn } from "$lib/utils"
  import { server, useElapsed } from "$lib/utils.svelte.js"
  import { toast } from "svelte-sonner"
  import Watch from "../@[username=user]/watch/+page.svelte"
  import PencilLine from "@lucide/svelte/icons/pencil-line"

  let { data } = $props()
  const start = data.stream.start
  let elapsed = () => (start ? useElapsed(() => start) : null)
  let title = $state(data.stream.title)
  let game = $state(data.stream.game)
  let open = $state(false)
</script>

<div class="flex flex-col p-2 gap-2">
  <div class="text-2xl font-bold">Dashboard</div>
  <div class="text-sm text-muted-foreground">Stream Preview</div>
  <div class="border rounded-md">
    <Watch
      data={{
        following: data.following,
        user: data.user,
        emotes: data.emotes,
        stream: data.stream,
        streamer: {
          colour: data.user.colour,
          displayName: data.user.displayName,
          followers: data.followers,
          following: data.following,
          username: data.user.username,
        },
      }}
    />
  </div>
  <ButtonGroup>
    <ButtonGroup>
      {#each [[elapsed?.() ?? "-", "Session"], [data.stream.viewers ?? "-", "Viewers"], [data.followers, "Followers"]] as [value, name] (name)}
        <Button variant="outline" class="flex flex-col gap-0 items-start py-2 px-4 h-auto w-28">
          <div class="text-base">{value}</div>
          <div class="text-muted-foreground text-xs">{name}</div>
        </Button>
      {/each}
    </ButtonGroup>
    <ButtonGroup>
      <Dialog bind:open>
        <DialogTrigger class={cn(buttonVariants(), "h-auto")}>
          <PencilLine />
          <div class="text-base">Stream Info</div>
        </DialogTrigger>
        <DialogContent>
          <form
            onsubmit={async (event) => {
              event.preventDefault()
              await server.self.updateStream({ title, game })
              await invalidateAll()
              toast.success("Stream info updated")
              open = false
            }}
            class="contents"
          >
            <DialogHeader>
              <DialogTitle>Stream info</DialogTitle>
              <DialogDescription>Edit</DialogDescription>
            </DialogHeader>˝
            <div class="">
              <FieldSet>
                <FieldGroup>
                  <Field>
                    <FieldLabel>Title</FieldLabel>
                    <Input bind:value={title} />
                  </Field>
                  <Field>
                    <FieldLabel>Game</FieldLabel>
                    <Input bind:value={game} />
                  </Field>
                </FieldGroup>
              </FieldSet>˝
            </div>
            <DialogFooter>
              <DialogClose class={buttonVariants({ variant: "outline" })} type="button">
                Cancel
              </DialogClose>
              <Button type="submit">Save changes</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </ButtonGroup>
  </ButtonGroup>
</div>
