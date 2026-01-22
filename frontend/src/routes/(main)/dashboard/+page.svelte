<script lang="ts">
  import { invalidateAll } from "$app/navigation"
  import { Button, buttonVariants } from "$lib/components/ui/button"
  import { ButtonGroup } from "$lib/components/ui/button-group"
  import {
    Dialog,
    DialogClose,
    DialogContent,
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
  import NotepadText from "@lucide/svelte/icons/notepad-text"
  import Plus from "@lucide/svelte/icons/plus"
  import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectTrigger,
  } from "$lib/components/ui/select"
  import { ScrollArea } from "$lib/components/ui/scroll-area"
  import ListRestart from "@lucide/svelte/icons/list-restart"
  import X from "@lucide/svelte/icons/x"
  import { Tooltip, TooltipContent, TooltipTrigger } from "$lib/components/ui/tooltip"
  import {
    InputGroup,
    InputGroupAddon,
    InputGroupButton,
    InputGroupInput,
  } from "$lib/components/ui/input-group"
  import Info from "@lucide/svelte/icons/info"

  let { data } = $props()
  const start = $derived(data.stream.start)
  let elapsed = useElapsed(() => start)
  // svelte-ignore state_referenced_locally
  let title = $state(data.stream.title)
  // svelte-ignore state_referenced_locally
  let game = $state(data.stream.game)
  let pollOpen = $state(false)
  let infoOpen = $state(false)

  let question = $state("")
  let options = $state(["Yes", "No"])
  const durations: [string, number][] = [
    ["30 sec", 30],
    ["60 sec", 60],
    ["2 min", 120],
    ["5 min", 300],
  ]
  let duration = $state(60)

  let watch: Watch
</script>

<div class="flex flex-col p-2 gap-2 grow min-h-0">
  <div class="text-2xl font-bold">Dashboard</div>
  <div class="border rounded-md grow min-h-0 flex flex-col">
    <Watch
      bind:this={watch}
      data={{
        following: data.following,
        user: data.user,
        emotes: data.emotes,
        stream: data.stream,
        profile: {
          colour: data.user.colour,
          displayName: data.user.displayName,
          followers: data.followers,
          following: data.following,
          username: data.user.username,
        },
        notify: data.notify,
      }}
    />
  </div>
  <div class="flex justify-between">
    <ButtonGroup>
      <ButtonGroup>
        {#each [[elapsed() ?? "-", "Session"], [data.stream.viewers ?? "-", "Viewers"], [data.followers, "Followers"]] as [value, name] (name)}
          <Button variant="outline" class="flex flex-col gap-0 items-start py-2 px-4 h-auto w-28">
            <div class="text-base">{value}</div>
            <div class="text-muted-foreground text-xs">{name}</div>
          </Button>
        {/each}
      </ButtonGroup>
      <ButtonGroup>
        <Dialog bind:open={pollOpen}>
          <DialogTrigger class={cn(buttonVariants(), "h-auto")}>
            <NotepadText />
            Start a Poll
          </DialogTrigger>
          <DialogContent>
            <form
              onsubmit={async (event) => {
                event.preventDefault()
                watch
                  .poll()
                  ?.send(
                    JSON.stringify({
                      type: "start",
                      question: question,
                      options: options,
                      duration: duration,
                    }),
                  )
                toast.success("Poll started")
                pollOpen = false
              }}
              class="contents"
            >
              <DialogHeader>
                <DialogTitle>Start a Poll</DialogTitle>
              </DialogHeader>
              <FieldSet>
                <FieldGroup>
                  <Field>
                    <FieldLabel>Question</FieldLabel>
                    <InputGroup>
                      <InputGroupInput bind:value={question} />
                      <InputGroupAddon align="inline-end">
                        <Tooltip>
                          <TooltipTrigger>
                            {#snippet child({ props })}
                              <InputGroupButton {...props} class="rounded-full" size="icon-xs">
                                <Info />
                              </InputGroupButton>
                            {/snippet}
                          </TooltipTrigger>
                          <TooltipContent>Poll questions can include emotes.</TooltipContent>
                        </Tooltip>
                      </InputGroupAddon>
                    </InputGroup>
                  </Field>
                  <Field>
                    <div class="flex justify-between items-center">
                      <FieldLabel>
                        Options ({options.length}) <Tooltip>
                          <TooltipTrigger>
                            {#snippet child({ props })}
                              <Button
                                {...props}
                                class="rounded-full size-6 p-0 has-[>svg]:p-0"
                                variant="ghost"
                              >
                                <Info />
                              </Button>
                            {/snippet}
                          </TooltipTrigger>
                          <TooltipContent>Poll options can include emotes.</TooltipContent>
                        </Tooltip>
                      </FieldLabel>
                      <ButtonGroup>
                        <Button
                          size="sm"
                          onclick={() => options.push(`Option ${options.length + 1}`)}
                        >
                          <Plus />
                          Add
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onclick={() => (options = ["Yes", "No"])}
                        >
                          <ListRestart />
                          Reset
                        </Button>
                      </ButtonGroup>
                    </div>
                    <ScrollArea>
                      <div class="flex flex-col gap-2 max-h-48 *:shrink-0 p-1">
                        {#each options as _, index (index)}
                          <ButtonGroup>
                            <Input bind:value={options[index]} />
                            <Tooltip>
                              <TooltipTrigger
                                class={buttonVariants({ variant: "outline" })}
                                onclick={() => options.splice(index, 1)}
                                disabled={options.length <= 2}
                              >
                                <X class="text-destructive" />
                              </TooltipTrigger>
                              <TooltipContent>Remove this option</TooltipContent>
                            </Tooltip>
                          </ButtonGroup>
                        {/each}
                      </div>
                    </ScrollArea>
                  </Field>
                  <Field>
                    <FieldLabel>Duration</FieldLabel>
                    <Select
                      type="single"
                      bind:value={
                        () => duration.toString(), (value) => (duration = parseInt(value))
                      }
                    >
                      <SelectTrigger>
                        {durations.find(([, value]) => value == duration)?.[0]}
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          {#each durations as [label, value] (value)}
                            <SelectItem value={value.toString()}>{label}</SelectItem>
                          {/each}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </Field>
                </FieldGroup>
              </FieldSet>
              <DialogFooter>
                <DialogClose class={buttonVariants({ variant: "outline" })} type="button">
                  Cancel
                </DialogClose>
                <Button type="submit" disabled={!question}>Start</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </ButtonGroup>
    </ButtonGroup>
    <ButtonGroup>
      <Dialog bind:open={infoOpen}>
        <DialogTrigger class={cn(buttonVariants(), "h-auto")}>
          <PencilLine />
          Stream Info
        </DialogTrigger>
        <DialogContent>
          <form
            onsubmit={async (event) => {
              event.preventDefault()
              await server.self.updateStream({ title, game })
              await invalidateAll()
              toast.success("Stream info updated")
              infoOpen = false
            }}
            class="contents"
          >
            <DialogHeader>
              <DialogTitle>Edit Stream Info</DialogTitle>
            </DialogHeader>
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
            </FieldSet>
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
  </div>
</div>
