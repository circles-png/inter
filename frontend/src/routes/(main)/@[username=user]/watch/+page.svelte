<script lang="ts">
  import { ResizableHandle, ResizablePane, ResizablePaneGroup } from "$lib/components/ui/resizable"
  import { apiBase, colours, parseMessage, server, useElapsed } from "$lib/utils.svelte"
  import { onMount } from "svelte"
  import type { Fragment, Message, MessageId } from "../../../../models/message"
  import { Avatar, AvatarFallback, AvatarImage } from "$lib/components/ui/avatar"
  import User from "@lucide/svelte/icons/user"
  import Timer from "@lucide/svelte/icons/timer"
  import Send from "@lucide/svelte/icons/send"
  import { Button, buttonVariants } from "$lib/components/ui/button"
  import { ButtonGroup } from "$lib/components/ui/button-group"
  import { Input } from "$lib/components/ui/input"
  import { Tooltip, TooltipContent, TooltipTrigger } from "$lib/components/ui/tooltip"
  import { HoverCard, HoverCardContent, HoverCardTrigger } from "$lib/components/ui/hover-card"
  import { resolve } from "$app/paths"
  import { invalidateAll } from "$app/navigation"
  import { ScrollArea } from "$lib/components/ui/scroll-area"
  import Reply from "@lucide/svelte/icons/reply"
  import Ellipsis from "@lucide/svelte/icons/ellipsis"
  import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
  } from "$lib/components/ui/dropdown-menu"
  import X from "@lucide/svelte/icons/x"
  import { cn } from "$lib/utils"

  let { data } = $props()
  let { displayName, colour, username } = $derived(data.streamer)
  let { title, game, start, viewers } = $derived(data.stream)

  let messages = $state<Message[]>([])
  let emotes = $derived(data.emotes)
  let chatInput: null | HTMLInputElement = $state(null)
  let focused = $state(false)
  let suggestions = $state<[string, [string, boolean]][]>([])
  let video: null | HTMLVideoElement = $state(null)
  let rtc: { chat: RTCDataChannel; connection: RTCPeerConnection } | null = $state(null)
  let elapsed = useElapsed(() => start)
  let messagesContainer: null | HTMLDivElement = $state(null)
  let replying: Extract<Message, { type: "message" }> | null = $state(null)

  function handleChatMessage(event: MessageEvent) {
    let data:
      | { type: "system"; message: string }
      | {
          type: "message"
          time: number
          message: string
          username: string
          colour: number
          replying: null | MessageId
          id: MessageId
        } = JSON.parse(event.data)
    switch (data.type) {
      case "system":
        messages.push({ type: "system", fragments: parseMessage(data.message, emotes) })
        break
      case "message":
        messages.push({
          type: "message",
          time: new Date(data.time),
          username: data.username,
          fragments: parseMessage(data.message, emotes),
          colour: data.colour,
          id: data.id,
          replying: data.replying,
        })
        break
    }
  }

  $effect(() => {
    if (messagesContainer && messages.length) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight
    }
  })

  onMount(() => {
    if (video) video.srcObject = new MediaStream()
    const connection = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    })

    let ws = new WebSocket(`${apiBase}/stream/${username}/ws`)
    ws.onmessage = async (event) => {
      const data:
        | { type: "connect"; sdp: RTCSessionDescriptionInit }
        | { type: "renegotiate"; sdp: RTCSessionDescriptionInit } = JSON.parse(event.data)

      if (data.type == "connect") {
        const answer = data.sdp
        await connection.setRemoteDescription(answer)
        ws.send(JSON.stringify({ type: "tracks" }))
      }

      if (data.type == "renegotiate") {
        const offer = data.sdp
        await connection.setRemoteDescription(offer)
        const answer = await connection.createAnswer()
        await connection.setLocalDescription(answer)
        ws.send(JSON.stringify({ type: "renegotiate", sdp: connection.localDescription }))
      }
    }

    messages.push({
      type: "system",
      fragments: parseMessage("Connecting to chat... Waiting", emotes),
    })

    ws.onopen = () => {
      connection.onicecandidate = (event) => {
        if (!event.candidate) return
        ws.send(
          JSON.stringify({
            type: "candidate",
            candidate: {
              candidate: event.candidate.candidate,
              sdpMid: event.candidate.sdpMid,
              sdpMLineIndex: event.candidate.sdpMLineIndex,
            },
          }),
        )
      }
      connection.ontrack = (event) => {
        if (video && video.srcObject && video.srcObject instanceof MediaStream) {
          video.srcObject.addTrack(event.track)
          video.play()
        }
      }
      connection.onnegotiationneeded = async () => {
        console.log("onnegotiationneeded")
        const offer = await connection.createOffer()
        await connection.setLocalDescription(offer)

        ws.send(
          JSON.stringify({
            type: "connect",
            sdp: connection.localDescription,
            token: await (await fetch(`${apiBase}/stream/auth`, { credentials: "include" })).text(),
          }),
        )
      }
      connection.oniceconnectionstatechange = () => {
        console.log("oniceconnectionstatechange", connection.iceConnectionState)
        if (connection.iceConnectionState === "disconnected") {
          messages.push({
            type: "system",
            fragments: parseMessage("Disconnected from server!", emotes),
          })
        }
      }
      connection.onsignalingstatechange = () => {
        console.log("onsignalingstatechange", connection.signalingState)
      }

      const chat = connection.createDataChannel("chat")
      chat.onmessage = handleChatMessage

      rtc = { chat, connection }
    }

    return () => {
      ws.close()
      connection.close()
    }
  })

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
</script>

<ResizablePaneGroup direction="horizontal" class="flex">
  <ResizablePane>
    <ScrollArea>
      <div class="relative flex flex-col gap-4 p-4">
        <video
          muted
          playsinline
          class="rounded-md aspect-video"
          style:background-color={colours[colour]}
          bind:this={video}
        ></video>
        {#if video}
          <Button
            class="absolute top-6 left-6"
            variant="secondary"
            onclick={() => {
              if (video) video.muted = false
            }}
          >
            Unmute
          </Button>
        {/if}
        <div class="flex justify-between text-sm">
          <div class="flex gap-4">
            <Avatar class="size-12">
              <AvatarImage src={server.user.avatar(username)} />
              <AvatarFallback class="bg-muted" />
            </Avatar>
            <div class="flex flex-col">
              <div class="font-bold text-base">{displayName || `@${username}`}</div>
              <div>{title}</div>
              <div class="text-muted-foreground">{game}</div>
            </div>
          </div>
          {#if elapsed()}
            <div class="flex flex-col text-red-400 font-mono text-xs">
              <div class="flex gap-2 items-center">
                <User class="h-4" />
                {viewers}
              </div>
              <div class="flex gap-2 items-center">
                <Timer class="h-4" />
                {elapsed()}
              </div>
            </div>
          {/if}
        </div>
      </div>
    </ScrollArea>
  </ResizablePane>
  <ResizableHandle />
  <ResizablePane class="flex flex-col" defaultSize={30}>
    <div class="flex flex-col py-4 grow overflow-auto" bind:this={messagesContainer}>
      {#each messages as message, index (index)}
        {@const { type, fragments } = message}
        <div class="flex flex-col">
          {#if message.type == "message" && message.replying}
            {@const replyingTo = messages.find(
              (other): other is Extract<Message, { type: "message" }> =>
                other.type == "message" && message.replying == other.id,
            )}
            {#if replyingTo}
              <div class="px-4">
                <div
                  class="text-xs [--spacing:0.2em] text-muted-foreground flex gap-2 items-center"
                >
                  <Reply class="size-6" />
                  <p>
                    Replying to
                    <span style="color: {colours[replyingTo.colour]}">{replyingTo.username}</span>:
                    {@render messageContent(replyingTo.fragments)}
                  </p>
                </div>
              </div>
            {/if}
          {/if}
          <div
            class={[
              "flex gap-2 items-center px-4 group",
              data.user
                && fragments.some(
                  (fragment) => fragment.type == "text" && fragment.text == data.user?.username,
                )
                && "bg-red-500/20 border-l-4 border-red-500",
              message.type == "message"
                && message.id === replying?.id
                && "border-l-4 border-blue-500 bg-blue-500/20",
              type === "system" && "text-xs text-muted-foreground [--spacing:0.2em]",
            ]}
          >
            <span class="text-xs text-muted-foreground">
              {#if message.type == "message"}
                {message.time.toLocaleTimeString()}
              {/if}
            </span>
            <p class="wrap-anywhere grow">
              {#if type === "message"}
                <HoverCard>
                  <HoverCardTrigger
                    style="color: {colours[message.colour]}"
                    href={resolve("/(main)/@[username=user]", { username: message.username })}
                  >
                    {message.username}:
                  </HoverCardTrigger>
                  <HoverCardContent class="flex gap-4 items-center">
                    <Avatar class="size-12">
                      <AvatarImage
                        src={server.user.avatar(message.username)}
                        alt={message.username}
                      />
                      <AvatarFallback class="bg-muted" />
                    </Avatar>
                    <div class="flex flex-col grow">
                      <div class="font-bold">
                        {(await server.user.user(message.username)).displayName}
                      </div>
                      <div class="text-sm text-muted-foreground">@{message.username}</div>
                    </div>
                    {#if data.user && message.username != data.user.username}
                      {#if data.following.some((following) => following.username == message.username)}
                        <Button
                          onclick={async () => {
                            server.user.unfollow(message.username)
                            await invalidateAll()
                          }}
                        >
                          Unfollow
                        </Button>
                      {:else}
                        <Button
                          onclick={async () => {
                            server.user.follow(message.username)
                            await invalidateAll()
                          }}
                        >
                          Follow
                        </Button>
                      {/if}
                    {/if}
                  </HoverCardContent>
                </HoverCard>
              {/if}
              {@render messageContent(fragments)}
            </p>
            {#if type === "message"}
              {@const reply = () => {
                replying = message
                chatInput?.focus()
              }}
              <ButtonGroup
                class="flex opacity-0 scale-90 group-hover:opacity-100 group-hover:scale-100 transition has-focus-visible:opacity-100 has-focus-visible:scale-100 has-data-[state=open]:opacity-100 has-data-[state=open]:scale-100"
              >
                <Button variant="ghost" size="sm" class="h-6 w-6" onclick={reply}>
                  <Reply class="size-4" />
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger
                    class={buttonVariants({ variant: "ghost", size: "sm", class: "h-6 w-6" })}
                  >
                    <Ellipsis class="size-4" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onclick={reply}>
                      <Reply class="size-4" />
                      <p>
                        Reply to <span style="color: {colours[message.colour]}">
                          {message.username}
                        </span>
                      </p>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </ButtonGroup>
            {/if}
          </div>
        </div>
      {/each}
    </div>
    {#if data.user}
      <div class="p-4 relative">
        <div class="flex flex-col">
          <div class="flex flex-col">
            {#if replying}
              <div class="p-2 bg-card border rounded-md rounded-b-none flex text-sm">
                <div class="flex flex-col grow">
                  <div class="">
                    Replying to
                    <span
                      style="color: {colours[(await server.user.user(replying.username)).colour]}"
                    >
                      {replying.username}
                    </span>
                  </div>
                  <div class="text-sm text-muted-foreground p-2 [--spacing:0.2em]">
                    {@render messageContent(replying.fragments)}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  class="size-6"
                  onclick={() => (replying = null)}
                >
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
                  const suggest = () => {
                    chatInput!.setRangeText(
                      suggestions[0][0] + " ",
                      chatInput!.value.slice(0, chatInput!.selectionEnd!).lastIndexOf(" ") + 1,
                      chatInput!.value.slice(chatInput!.selectionEnd!).indexOf(" ")
                        + chatInput!.selectionEnd!
                        + 1,
                      "end",
                    )
                    suggestions = []
                  }
                  if (event.key === "Enter") {
                    if (suggestions.length) {
                      suggest()
                    } else {
                      sendMessage()
                    }
                  } else if (event.key === "Tab") {
                    if (suggestions.length) {
                      event.preventDefault()
                      suggest()
                    }
                  } else if (event.key === "Escape") {
                    event.preventDefault()
                    suggestions = []
                  }
                }}
                onfocus={() => (focused = true)}
                onblur={() => (focused = false)}
              />
              <Button size="icon" variant="secondary" onclick={sendMessage}>
                <Send />
              </Button>
            </ButtonGroup>
          </div>
        </div>
        <div class="absolute bottom-full left-0 px-4">
          {#key suggestions}
            {#if suggestions.length && focused}
              <div
                class="grid grid-cols-5 *:justify-start bg-card rounded-md border shadow-md p-2 gap-1 max-h-40 overflow-y-auto"
              >
                {#each suggestions as [name, [url]] (name)}
                  <Tooltip>
                    <TooltipTrigger>
                      <img class="inline-block h-6" src={url} alt={name} />
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
  </ResizablePane>
</ResizablePaneGroup>

{#snippet messageContent(fragments: Fragment[])}
  {#each fragments as fragment, index (index)}
    {#if fragment.type === "text"}
      <span>{fragment.text}</span>
    {:else if fragment.type === "emote"}
      <Tooltip>
        <TooltipTrigger class="inline-flex items-center">
          <img class="inline-block h-5" src={fragment.url} alt={fragment.name} />
        </TooltipTrigger>
        <TooltipContent class="flex flex-col items-center">
          <img class="inline-block h-10" src={fragment.url} alt={fragment.name} />
          {fragment.name}
        </TooltipContent>
      </Tooltip>
    {:else if fragment.type === "emote-stack"}
      <Tooltip>
        <TooltipTrigger class="inline-flex items-center">
          <span class="inline-grid place-items-center h-6">
            {#each fragment.emotes as emote, index (index)}
              <img
                class="inline-block h-5 col-start-1 row-start-1"
                src={emote.url}
                alt={emote.name}
              />
            {/each}
          </span>
        </TooltipTrigger>
        <TooltipContent class="flex flex-col items-center">
          <div class="-rotate-x-20 rotate-y-40 relative h-30 w-60 perspective-distant transform-3d">
            {#each fragment.emotes as emote, index (index)}
              <img
                class="h-10 absolute w-30 object-contain"
                src={emote.url}
                alt={emote.name}
                style:transform={`translateZ(${index * 40}px)`}
              />
            {/each}
          </div>
          {#each fragment.emotes as emote, index (index)}
            <span>{emote.name}</span>
          {/each}
        </TooltipContent>
      </Tooltip>
    {/if}
  {/each}
{/snippet}
