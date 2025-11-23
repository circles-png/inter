<script lang="ts">
  import { page } from "$app/state"
  import Button from "$lib/components/ui/button/button.svelte"
  import Input from "$lib/components/ui/input/input.svelte"
  import { ResizablePane } from "$lib/components/ui/resizable"
  import ResizableHandle from "$lib/components/ui/resizable/resizable-handle.svelte"
  import ResizablePaneGroup from "$lib/components/ui/resizable/resizable-pane-group.svelte"
  import { getStreamEndpoint } from "$lib/utils.svelte"
  import Header from "../../stories/Header.svelte"

  type Emote = { name: string; url: string }
  type Fragment = ({ type: Emote } & Emote) | { type: "text"; text: string; name: string }
  type Message = { time: string; message: Fragment[] }

  let chat = $state<Message[]>([])
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
  const { data } = $props()
  const username = data.username
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
            chat.push(data.message)
            break
        }
      }

      let connect = async () => {
        let offer = await connection.createOffer()
        connection.setLocalDescription(offer)
        let response = await fetch(
          getStreamEndpoint(page.url.hostname, "http", `stream/${username}/rx`),
          { method: "POST", headers: { "Content-Type": "application/sdp" }, body: offer.sdp },
        )
        let answer = await response.text()
        await connection.setRemoteDescription(
          new RTCSessionDescription({ sdp: answer, type: "answer" }),
        )
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

        const ws = new WebSocket(
          getStreamEndpoint(page.url.hostname, "ws", `stream/${username}/ws`),
        )
        await new Promise((resolve) => {
          ws.onopen = resolve
        })
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

<Header />

<main class="flex gap-2 flex-col lg:flex-row h-full grow">
  <ResizablePaneGroup direction="horizontal">
    <ResizablePane class="p-4 flex flex-col relative">
      <video autoplay muted playsinline class="rounded-md" bind:this={stream}></video>
      <button
        class="absolute top-4 left-4 px-4 py-2 bg-black rounded-md"
        onclick={(event) => {
          stream.muted = false
          event.currentTarget.remove()
        }}>Unmute</button
      >
    </ResizablePane>
    <ResizableHandle />
    <ResizablePane class="p-4 flex flex-col">
      <div class="grow p-4 overflow-y-auto"></div>
      <div class="flex gap-4 relative">
        <div class="p-4 rounded-md bottom-full inset-x-0 absolute bg-black"></div>
        <Input
          class="p-4 border h-12 rounded-md grow"
          placeholder="Type a message..."
          bind:value={chatInput}
        />
        <Button
          class="size-12"
          onclick={(event) => {
            if (!event.currentTarget) return
            if (!chatInput) return
            if (!connectionState) return
            connectionState.channel.send(chatInput)
            chatInput = ""
            suggestions = []
          }}
        ></Button>
      </div>
    </ResizablePane>
  </ResizablePaneGroup>
</main>
