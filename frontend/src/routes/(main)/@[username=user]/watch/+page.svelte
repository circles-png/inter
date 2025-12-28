<script lang="ts">
  import { ResizableHandle, ResizablePane, ResizablePaneGroup } from "$lib/components/ui/resizable"
  import { apiBase, colours, parseMessage, server } from "$lib/utils.svelte"
  import { onMount } from "svelte"
  import type { Message } from "../../../../models/message"
  import { Avatar, AvatarFallback, AvatarImage } from "$lib/components/ui/avatar"
  import User from "@lucide/svelte/icons/user"
  import Timer from "@lucide/svelte/icons/timer"
  import Send from "@lucide/svelte/icons/send"
  import { Button } from "$lib/components/ui/button"
  import { ButtonGroup } from "$lib/components/ui/button-group"
  import { Input } from "$lib/components/ui/input"
  import { Tooltip, TooltipContent, TooltipTrigger } from "$lib/components/ui/tooltip"
  import { HoverCard, HoverCardContent, HoverCardTrigger } from "$lib/components/ui/hover-card"
  import { resolve } from "$app/paths"
  import { invalidateAll } from "$app/navigation"
  import { ScrollArea } from "$lib/components/ui/scroll-area"

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
  let elapsed = $state("")
  let messagesContainer: null | HTMLDivElement = $state(null)

  function handleChatMessage(event: MessageEvent) {
    let data:
      | { type: "system"; message: string }
      | { type: "message"; time: number; message: string; username: string; colour: number } =
      JSON.parse(event.data)
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
    const connection = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    })

    const ws = new WebSocket(`${apiBase}/stream/${username}/ws`)
    ws.onmessage = async (event) => {
      const data: { type: "stream_started" } | { type: "connect"; sdp: RTCSessionDescriptionInit } =
        JSON.parse(event.data)

      if (data.type == "stream_started") {
        connection.restartIce()
      } else if (data.type == "connect") {
        const answer = data.sdp
        await connection.setRemoteDescription(answer)
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
        if (video) video.srcObject = event.streams[0]
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
      }
      connection.onsignalingstatechange = () => {
        console.log("onsignalingstatechange", connection.signalingState)
      }

      const chat = connection.createDataChannel("chat")
      chat.onmessage = handleChatMessage

      rtc = { chat, connection }
    }

    const interval = setInterval(() => {
      elapsed = start
        ? new Date(Date.now() - start).toLocaleTimeString("en-GB", {
            hour12: false,
            timeZone: "UTC",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          })
        : ""
    }, 1000)

    return () => {
      ws.close()
      connection.close()
      clearInterval(interval)
    }
  })

  const updateSuggestions = () => {
    const word = chatInput!.value.slice(0, chatInput!.selectionEnd!).split(/\s/).pop()
    if (!word) {
      suggestions = []
      return
    }
    suggestions = Object.entries(emotes)
      .filter(([name]) => name.startsWith(word))
      .slice(0, 5)
  }

  const sendMessage = () => {
    if (!chatInput?.value) return
    if (!rtc) return
    rtc.chat.send(chatInput.value)
    chatInput.value = ""
    suggestions = []
  }
</script>

<ResizablePaneGroup direction="horizontal" class="flex">
  <ResizablePane>
    <ScrollArea>
      <div class="relative flex flex-col gap-4 p-4">
        <video
          autoplay
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
          {#if elapsed}
            <div class="flex flex-col text-red-400 font-mono text-xs">
              <div class="flex gap-2 items-center">
                <User class="h-4" />
                {viewers}
              </div>
              <div class="flex gap-2 items-center">
                <Timer class="h-4" />
                {elapsed}
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
        {@const { time, username, colour } =
          message.type === "message" ? message : { time: undefined, username: "", colour: -1 }}
        <div
          class={[
            "flex gap-2 items-center px-4",
            data.user
              && fragments.some(
                (fragment) => fragment.type == "text" && fragment.text == data.user?.username,
              )
              && "bg-red-500/20 border-l-4 border-red-500",
            type === "system" && "text-xs text-muted-foreground [--spacing:0.2em]",
          ]}
        >
          <span class="text-xs text-muted-foreground">
            {time?.toLocaleTimeString()}
          </span>
          <p class="wrap-anywhere">
            {#if type === "message"}
              <HoverCard>
                <HoverCardTrigger
                  style="color: {colours[colour]}"
                  href={resolve("/(main)/@[username=user]", { username })}
                >
                  {username}:
                </HoverCardTrigger>
                <HoverCardContent class="flex gap-4 items-center">
                  <Avatar class="size-12">
                    <AvatarImage src={server.user.avatar(username)} alt={username} />
                    <AvatarFallback class="bg-muted" />
                  </Avatar>
                  <div class="flex flex-col grow">
                    <div class="font-bold">{(await server.user.user(username)).displayName}</div>
                    <div class="text-sm text-muted-foreground">@{username}</div>
                  </div>
                  {#if data.user && username != data.user.username}
                    {#if data.following.some((following) => following.username == username)}
                      <Button
                        onclick={async () => {
                          server.user.unfollow(username)
                          await invalidateAll()
                        }}
                      >
                        Unfollow
                      </Button>
                    {:else}
                      <Button
                        onclick={async () => {
                          server.user.follow(username)
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
                    <div
                      class="-rotate-x-20 rotate-y-40 relative h-30 w-60 perspective-distant transform-3d"
                    >
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
          </p>
        </div>
      {/each}
    </div>
    {#if data.user}
      <div class="p-4 relative">
        <ButtonGroup class="w-full">
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
        <div class="absolute bottom-full left-0 px-4">
          {#key suggestions}
            {#if suggestions.length && focused}
              <div class="flex flex-col *:justify-start bg-card rounded-md border shadow-md p-2">
                {#each suggestions as [name, [url]], index (index)}
                  <div class="flex gap-2 p-2 rounded-md" class:bg-accent={index === 0}>
                    <img class="inline-block h-6" src={url} alt={name} />
                    <span>{name}</span>
                  </div>
                {/each}
              </div>
            {/if}
          {/key}
        </div>
      </div>
    {/if}
  </ResizablePane>
</ResizablePaneGroup>
