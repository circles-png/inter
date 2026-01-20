<script lang="ts">
  import Send from "@lucide/svelte/icons/send"
  import { ButtonGroup } from "$lib/components/ui/button-group"
  import { Input } from "$lib/components/ui/input"
  import ChatMessages from "./ChatMessages.svelte"
  import X from "@lucide/svelte/icons/x"
  import { Button } from "$lib/components/ui/button"
  import { Tooltip, TooltipContent, TooltipTrigger } from "$lib/components/ui/tooltip"
  import Fragments from "./Fragments.svelte"
  import { cn } from "$lib/utils"
  import type { Message } from "../../../../models/message"
  import type { User } from "../../../../models/user"
  import { onMount } from "svelte"
  import { parseMessage } from "$lib/utils.svelte"
  import Clock4 from "@lucide/svelte/icons/clock-4"
  import { Toggle } from "$lib/components/ui/toggle"

  let {
    rtc = $bindable(),
    user,
    emotes,
    messages = $bindable(),
  }: {
    rtc: { chat: RTCDataChannel } | null
    user: User | null
    emotes: { [key: string]: [string, boolean] }
    messages: Message[]
  } = $props()
  let focused = $state(false)
  let suggestions = $state<[string, [string, boolean]][]>([])
  let chatInput: null | HTMLInputElement = $state(null)
  let replying: Extract<Message, { type: "message" }> | null = $state(null)
  let showTimes: boolean = $state(false)

  const updateSuggestions = () => {
    const word = chatInput!.value.slice(0, chatInput!.selectionEnd!).split(/\s/).pop()
    if (!word) {
      suggestions = []
      return
    }
    suggestions = Object.entries(emotes).filter(([name]) =>
      name.toLowerCase().startsWith(word.toLowerCase()),
    )
  }

  const sendMessage = () => {
    if (!chatInput?.value) return
    if (!rtc) return
    rtc.chat.send(JSON.stringify({ text: chatInput.value, replying: replying?.id ?? null }))
    chatInput.value = ""
    suggestions = []
    replying = null
  }

  const suggest = (suggestion: string) => {
    chatInput!.setRangeText(
      suggestion + " ",
      chatInput!.value.slice(0, chatInput!.selectionEnd!).lastIndexOf(" ") + 1,
      chatInput!.value.slice(chatInput!.selectionEnd!).indexOf(" ") + chatInput!.selectionEnd! + 1,
      "end",
    )
    suggestions = []
  }

  onMount(() => {
    messages.push({
      type: "system",
      fragments: parseMessage("Connecting to chat... Waiting", emotes),
    })
  })
</script>

<div class="flex px-4 items-center">
  <h1 class="grow text-xl font-bold">Live chat</h1>
  <Tooltip>
    <TooltipTrigger>
      {#snippet child({ props })}
        <Toggle size="sm" bind:pressed={showTimes} {...props}>
          <Clock4 />
        </Toggle>
      {/snippet}
    </TooltipTrigger>
    <TooltipContent>Timestamps</TooltipContent>
  </Tooltip>
</div>
<ChatMessages bind:messages {user} bind:replying {chatInput} {showTimes} />
{#if user}
  <div class="px-4 relative">
    <div class="flex flex-col">
      {#if replying}
        <div class="p-2 bg-card border border-b-0 rounded-md rounded-b-none flex text-sm">
          <div class="flex flex-col grow">
            <div class="text-xs">
              <span class="text-green-500">Replying</span> to {replying.username}
            </div>
            <div class="text-sm text-muted-foreground p-2 [--spacing:0.2em]">
              {#if !replying.filtered}
                <Fragments fragments={replying.fragments} />
              {:else}
                <span class="text-muted-foreground">
                  <Button
                    variant="ghost"
                    size="sm"
                    class="text-xs p-1 h-auto peer"
                    onclick={() => replying && (replying.filtered = false)}
                  >
                    Show filtered message
                  </Button>
                </span>
              {/if}
            </div>
          </div>
          <Button variant="ghost" size="icon" class="size-6" onclick={() => (replying = null)}>
            <X />
          </Button>
        </div>
      {/if}
      <ButtonGroup class={cn(replying && "**:rounded-t-none")}>
        <Input
          bind:ref={chatInput}
          oninput={updateSuggestions}
          onselectionchange={updateSuggestions}
          onkeydown={(event) => {
            if (event.key === "Enter") {
              sendMessage()
            } else if (event.key === "Tab") {
              if (suggestions.length) {
                event.preventDefault()
                suggest(suggestions[0][0])
              }
            } else if (event.key === "Escape") {
              event.preventDefault()
              if (!suggestions.length) {
                replying = null
                chatInput?.blur()
              }
              suggestions = []
            }
          }}
          onfocus={() => (focused = true)}
          onblur={() => (focused = false)}
        />
        <Button
          size="icon"
          variant="secondary"
          onclick={sendMessage}
          class={cn(replying && "text-green-300 bg-green-900 hover:bg-green-950", "transition")}
        >
          <Send />
        </Button>
      </ButtonGroup>
    </div>
    <div class="absolute bottom-full left-0 px-4">
      {#key suggestions}
        {#if suggestions.length && focused}
          <div
            class="grid grid-cols-[repeat(5,auto)] bg-card rounded-md border shadow-md p-2 gap-1 max-h-60 overflow-y-auto"
          >
            {#each suggestions as [name, [url]] (name)}
              <Tooltip>
                <TooltipTrigger>
                  {#snippet child({ props })}
                    <Button
                      {...props}
                      onmousedown={(event: Event) => event.preventDefault()}
                      onclick={() => {
                        suggest(name)
                      }}
                      variant="ghost"
                      class="p-1"
                    >
                      <img class="inline-block h-6" src={url} alt={name} />
                    </Button>
                  {/snippet}
                </TooltipTrigger>
                <TooltipContent>
                  {name}
                </TooltipContent>
              </Tooltip>
            {/each}
          </div>
        {/if}
      {/key}
    </div>
  </div>
{/if}
