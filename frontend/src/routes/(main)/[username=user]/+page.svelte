<script lang="ts">
  import { page } from "$app/state"
  import { ResizablePane } from "$lib/components/ui/resizable"
  import ResizableHandle from "$lib/components/ui/resizable/resizable-handle.svelte"
  import ResizablePaneGroup from "$lib/components/ui/resizable/resizable-pane-group.svelte"
  import { getApiEndpoint } from "$lib/utils.svelte"
  import type { Emote } from "../../../models/emote"
  import type { Message } from "../../../models/message"
  import type { User } from "../../../models/user"
  import Chat from "../../../stories/Chat.svelte"
  import Details from "../../../stories/Details.svelte"

  let user = $state<User>()
  let content = $state({
    creator: {
      id: 1,
      username: "Viewer",
      avatar: "http://picsum.photos/200",
      colour: "#aaf",
      roles: [],
    },
    title: "Sample Stream",
    description: "This is a sample stream description.",
    game: "Sample Game",
    viewerCount: 1234,
    duration: "12:34:56",
  })

  let messages = $state<{ message: Message; user: User }[]>([])
  let emotes = $state<Emote[]>([])
  let chatInput = $state("")
  let suggestions = $derived.by(() => {
    const parts = chatInput.split(" ")
    if (parts.length === 0) return []
    const last = parts[parts.length - 1]
    if (!last) return []

    return emotes.filter((emote) => emote.name.startsWith(last)).slice(0, 5)
  })
  let stream = null as unknown as HTMLVideoElement
  let connectionState: { channel: RTCDataChannel; connection: RTCPeerConnection } | null = null
  const { username } = page.params
  $effect(() => {
    ;(async () => {
      const connection = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      })
      connection.addTransceiver("video", { direction: "recvonly" })
      connection.addTransceiver("audio", { direction: "recvonly" })
      const channel = connection.createDataChannel("chat")
      connectionState = { channel, connection }
      channel.onmessage = (event) => {
        let data = JSON.parse(event.data)
        switch (data.type) {
          case "emotes":
            emotes = data.emotes
            break
          case "message":
            messages.push({ message: data.message, user: data.user })
            break
        }
      }

      let connect = async () => {
        let offer = await connection.createOffer()
        connection.setLocalDescription(offer)
        let response = await fetch(
          getApiEndpoint(page.url.hostname, "http", `stream/${username}/rx`),
          { method: "POST", headers: { "Content-Type": "application/sdp" }, body: offer.sdp },
        )
        let answer = await response.text()
        await connection.setRemoteDescription(
          new RTCSessionDescription({ sdp: answer, type: "answer" }),
        )
      }

      const ws = new WebSocket(getApiEndpoint(page.url.hostname, "ws", `stream/${username}/ws`))
      await new Promise((resolve) => {
        ws.onopen = resolve
      })
      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data)
        console.log(data)
        switch (data.type) {
          case "stream_started":
            await connect()
            break
        }
      }

      connection.ontrack = (event) => {
        console.log("Received track", event.streams[0])
        stream.srcObject = event.streams[0]
      }
      connection.onconnectionstatechange = async () => {
        console.log("onconnectionstatechange", connection.connectionState)
        if (connection.connectionState === "disconnected") {
          await connect()
        }
      }
      connection.ondatachannel = (event) => {
        console.log("ondatachannel", event)
      }
      connection.onicecandidate = async (event) => {
        console.log("onicecandidate", event)
        if (!event.candidate || !event.candidate.component) return

        ws.send(
          JSON.stringify({
            type: "candidate",
            candidate: {
              component: { rtp: 1, rtcp: 2 }[event.candidate.component],
              foundation: event.candidate.foundation,
              ip: event.candidate.address,
              port: event.candidate.port,
              priority: event.candidate.priority,
              protocol: event.candidate.protocol,
              type: event.candidate.type,
              relatedAddress: event.candidate.relatedAddress,
              relatedPort: event.candidate.relatedPort,
              sdpMid: event.candidate.sdpMid,
              sdpMLineIndex: event.candidate.sdpMLineIndex,
              tcpType: event.candidate.tcpType,
            },
          }),
        )
      }
      connection.onicecandidateerror = (event) => {
        console.log("onicecandidateerror", event)
      }
      connection.oniceconnectionstatechange = () => {
        console.log("oniceconnectionstatechange", connection.iceConnectionState)
      }
      connection.onicegatheringstatechange = () => {
        console.log("onicegatheringstatechange", connection.iceGatheringState)
      }
      connection.onnegotiationneeded = (event) => {
        console.log("onnegotiationneeded", event)
      }
      connection.onsignalingstatechange = () => {
        console.log("onsignalingstatechange", connection.signalingState)
      }

      await connect()
    })()
  })
</script>

<ResizablePaneGroup direction="horizontal" class="flex">
  <ResizablePane class="relative flex flex-col gap-4 p-4">
    <video autoplay muted playsinline class="rounded-md" bind:this={stream}></video>
    <button
      class="absolute top-4 left-4 px-4 py-2 bg-black rounded-md"
      onclick={(event) => {
        stream.muted = false
        event.currentTarget.remove()
      }}>Unmute</button
    >
    <Details {content} />
  </ResizablePane>
  <ResizableHandle />
  <ResizablePane class="flex flex-col *:grow">
    <Chat
      {messages}
      bind:chatInput
      onSend={() => {
        if (!chatInput) return
        if (!connectionState) return
        connectionState.channel.send(chatInput)
        chatInput = ""
        suggestions = []
      }}
    />
  </ResizablePane>
</ResizablePaneGroup>
