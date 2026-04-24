<script lang="ts">
  import { ResizableHandle, ResizablePane, ResizablePaneGroup } from "$lib/components/ui/resizable"
  import {
    apiBase,
    colours,
    isURL,
    parseMessage,
    server,
    useElapsed,
    useModeration,
    useNow,
  } from "$lib/utils.svelte"
  import { onMount } from "svelte"
  import { Avatar, AvatarFallback, AvatarImage } from "$lib/components/ui/avatar"
  import User from "@lucide/svelte/icons/user"
  import Timer from "@lucide/svelte/icons/timer"
  import { Button, buttonVariants } from "$lib/components/ui/button"
  import { ScrollArea } from "$lib/components/ui/scroll-area"

  import { cn } from "$lib/utils"
  import { IsMobile } from "$lib/hooks/is-mobile.svelte.js"

  import { Separator } from "$lib/components/ui/separator"
  import type { Poll } from "../../../../models/poll"
  import { Duration } from "luxon"
  import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
  } from "$lib/components/ui/collapsible"
  import ListChevronsUpDown from "@lucide/svelte/icons/list-chevrons-up-down"
  import ListChevronsDownUp from "@lucide/svelte/icons/list-chevrons-down-up"
  import MessageContent from "./Fragments.svelte"
  import Chat from "./Chat.svelte"
  import type { Message, MessageId } from "../../../../models/message.ts"

  let { data } = $props()
  let { displayName, colour, username } = $derived(data.profile)
  let { title, game, start, viewers } = $derived(data.stream)
  let emotes = $state({})
  let roles = $derived(data.roles)

  let video: HTMLVideoElement
  let rtc: { chat: RTCDataChannel; poll: RTCDataChannel; connection: RTCPeerConnection } | null =
    $state(null)
  let elapsed = useElapsed(() => start)
  let isMobile = new IsMobile()
  let polls = $state<Poll[]>([])
  let messages = $state<Message[]>([])
  const now = useNow()
  const moderation = useModeration()

  export function poll() {
    return rtc?.poll
  }

  $effect(() => {
    if (
      polls.some(
        (poll) =>
          (poll.start + poll.duration) * 1000 - now().getTime() <= 0
          && poll.options.some((option) => option.percent === undefined),
      )
    ) {
      rtc?.poll.send(JSON.stringify({ type: "update" }))
    }
  })

  onMount(() => {
    let connection = createConnection()
    let ws = createWebSocket()
    function createConnection() {
      return new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] })
    }
    function createWebSocket() {
      let newWs = (() => {
        const newWs = new WebSocket(`${apiBase}/stream/${username}/ws`)
        newWs.onerror = () => {
          setTimeout(() => {
            ws = createWebSocket()
          }, 1000)
        }
        return newWs
      })()
      if (!newWs) return
      newWs.onmessage = async (event) => {
        const data: { type: "connect"; sdp: RTCSessionDescriptionInit } | { type: "roles" } =
          JSON.parse(event.data)

        if (data.type == "connect") {
          const answer = data.sdp
          await connection.setRemoteDescription(answer)
        }

        if (data.type == "roles") {
          messages = messages.map((message) =>
            message.type == "message"
              ? {
                  ...message,
                  roles: server.user
                    .getRoles(message.username, username)
                    .then((userRoles) =>
                      userRoles.map((role) => roles.find(({ id }) => id === role)!),
                    ),
                }
              : message,
          )
        }
      }

      newWs.onopen = () => {
        connection.onicecandidate = (event) => {
          if (!event.candidate) return
          if (!newWs) return
          newWs.send(
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
          console.log("track", event.streams[0])
          if (!video.srcObject) {
            video.srcObject = event.streams[0]
          }
        }
        connection.onnegotiationneeded = async () => {
          console.log("onnegotiationneeded")
          const offer = await connection.createOffer()
          await connection.setLocalDescription(offer)

          if (!newWs) return
          newWs.send(
            JSON.stringify({
              type: "connect",
              sdp: connection.localDescription,
              token: await (
                await fetch(`${apiBase}/stream/auth`, { credentials: "include" })
              ).text(),
            }),
          )
        }
        connection.oniceconnectionstatechange = () => {
          console.log("oniceconnectionstatechange", connection.iceConnectionState)
          if (connection.iceConnectionState === "disconnected") {
            messages.push({ type: "system", text: "Disconnected from server, reconnecting..." })
            connection.close()
            connection = createConnection()
            if (ws) ws.close()
            ws = createWebSocket()
          }
        }
        connection.onsignalingstatechange = () => {
          console.log("onsignalingstatechange", connection.signalingState)
        }

        const chat = connection.createDataChannel("chat")
        chat.onmessage = (event) => {
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
          const fragments = parseMessage(data.message, emotes)
          switch (data.type) {
            case "system":
              messages.push({ type: "system", text: data.message })
              break
            case "message":
              messages.push({
                type: "message",
                time: new Date(data.time),
                username: data.username,
                fragments,
                colour: data.colour,
                id: data.id,
                replying: data.replying,
                filtered:
                  (data.username != username && moderation.match(data.message))
                  || (moderation.links.block
                    && fragments.some(
                      (fragment) => fragment.type == "text" && isURL(fragment.text),
                    )),
                roles: server.user
                  .getRoles(data.username, username)
                  .then((userRoles) =>
                    userRoles.map((role) => roles.find(({ id }) => id === role)!),
                  ),
              })
              break
          }
        }
        const poll = connection.createDataChannel("poll")
        poll.onmessage = (event) => {
          const data: { type: "update"; polls: Poll[] } = JSON.parse(event.data)
          switch (data.type) {
            case "update":
              polls = data.polls
              break
          }
        }

        connection.addTransceiver("video", { direction: "recvonly" })
        connection.addTransceiver("audio", { direction: "recvonly" })

        rtc = { chat, poll, connection }
      }
      return newWs
    }

    server.emotes().then((data) => (emotes = data))
    return () => {
      connection.close()
      if (ws) ws.close()
    }
  })
</script>

{#if isMobile.current}
  {@render stream()}
  <div class="flex flex-col grow min-h-0">{@render rightSidebar()}</div>
{:else}
  <ResizablePaneGroup direction="horizontal" class="flex grow">
    <ResizablePane minSize={50}>
      <ScrollArea>
        {@render stream()}
      </ScrollArea>
    </ResizablePane>
    <ResizableHandle />
    <ResizablePane
      class="flex flex-col"
      defaultSize={30}
      collapsible
      collapsedSize={0}
      minSize={20}
    >
      {@render rightSidebar()}
    </ResizablePane>
  </ResizablePaneGroup>
{/if}

{#snippet stream()}
  <div class="flex flex-col relative md:p-2">
    <video
      muted
      controls
      playsinline
      autoplay
      class="aspect-video md:rounded-md"
      style:background-color={colours[colour]}
      bind:this={video}
    ></video>
    <div class="flex text-sm p-4 gap-4">
      <Avatar class="size-12">
        <AvatarImage src={server.user.avatar(username)} />
        <AvatarFallback class="bg-muted" />
      </Avatar>
      <div class="flex flex-col md:flex-row md:justify-between gap-y-1 grow">
        <div
          class="flex md:flex-col wrap-anywhere gap-x-1 items-center md:items-stretch self-start flex-wrap"
        >
          <div class="font-bold text-base">{displayName || `@${username}`}</div>
          <div class="md:hidden">&middot;</div>
          <div>{title}</div>
          <div class="md:hidden">&middot;</div>
          <div class="text-muted-foreground">{game}</div>
        </div>
        {#if elapsed()}
          <div class="flex md:flex-col text-red-400 font-mono text-xs gap-x-4">
            <div class="flex md:gap-2 items-center">
              <User class="h-4" />
              {viewers}
            </div>
            <div class="flex md:gap-2 items-center">
              <Timer class="h-4" />
              {elapsed()}
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/snippet}

{#snippet rightSidebar()}
  <ResizablePaneGroup direction="vertical">
    {#if polls.length}
      <ResizablePane minSize={10} collapsible collapsedSize={0} defaultSize={20}>
        <ScrollArea>
          <div class="p-4 flex flex-col gap-2">
            {#each polls as { id, question, options, duration, start }, pollIndex (pollIndex)}
              <Collapsible open={true} class="group">
                <div
                  class="border rounded-md p-4 flex flex-col gap-2 group-data-[state=closed]:p-0 transition-[padding]"
                >
                  <div class="flex">
                    <div
                      class="flex group-data-[state=open]:flex-col grow group-data-[state=closed]:gap-2 group-data-[state=closed]:p-2 transition-[padding] min-w-0"
                    >
                      <h1
                        class="font-bold text-xs group-data-[state=open]:text-sm flex gap-2 group-data-[state=closed]:gap-1"
                      >
                        <span class="text-muted-foreground">Poll</span>
                        {#if (start + duration) * 1000 - now().getTime() > 0}
                          <span class="font-mono">
                            {Duration.fromMillis(
                              (start + duration) * 1000 - now().getTime(),
                            ).toFormat("mm:ss")}
                          </span>
                          <span>remaining</span>
                        {:else}
                          <span>Ended</span>
                        {/if}
                      </h1>
                      <h2
                        class="font-bold text-xs group-data-[state=closed]:[--spacing:0.2em] group-data-[state=open]:text-lg wrap-anywhere group-data-[state=closed]:truncate min-w-0"
                      >
                        <MessageContent fragments={parseMessage(question, emotes)} />
                      </h2>
                    </div>
                    <CollapsibleTrigger
                      class={cn(
                        buttonVariants({ variant: "ghost", size: "sm" }),
                        "group-data-[state=closed]:rounded-l-none",
                      )}
                    >
                      <ListChevronsUpDown class="group-data-[state=open]:hidden" />
                      <ListChevronsDownUp class="hidden group-data-[state=open]:block" />
                    </CollapsibleTrigger>
                  </div>
                  <CollapsibleContent class="flex flex-col gap-2">
                    <Separator />
                    <div class="grow flex flex-col gap-1">
                      {#each options as { text, percent }, optionIndex (optionIndex)}
                        {#if percent !== undefined}
                          <Button
                            class="justify-start"
                            size="sm"
                            variant="outline"
                            style="background: linear-gradient(to right, {colours[
                              colour
                            ]} {percent}%, transparent {percent}%) no-repeat padding-box"
                          >
                            <span class="truncate">
                              <MessageContent fragments={parseMessage(text, emotes)} />
                            </span>
                            <span class="text-muted-foreground">
                              {percent}%
                            </span>
                          </Button>
                        {:else}
                          <Button
                            variant="outline"
                            class="justify-start"
                            size="sm"
                            disabled={!data.user}
                            onclick={() => {
                              rtc?.poll.send(
                                JSON.stringify({ type: "vote", poll: id, option: optionIndex }),
                              )
                            }}
                          >
                            <span class="truncate">
                              <MessageContent fragments={parseMessage(text, emotes)} />
                            </span>
                          </Button>
                        {/if}
                      {/each}
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
            {/each}
          </div>
        </ScrollArea>
      </ResizablePane>
    {/if}
    <ResizableHandle />
    <ResizablePane
      class="flex flex-col py-4 grow gap-4 border-t md:border-t-0 min-h-0"
      minSize={20}
    >
      <Chat bind:rtc user={data.user} {emotes} {username} {roles} bind:messages />
    </ResizablePane>
  </ResizablePaneGroup>
{/snippet}
