<script lang="ts">
  import Message from "./Message.svelte"
  import "../app.css"
  import type { Message as MessageType } from "../models/message"
  import type { User } from "../models/user"
  import Input from "$lib/components/ui/input/input.svelte"
  import Button from "$lib/components/ui/button/button.svelte"
  import Send from "@lucide/svelte/icons/send"

  interface Props {
    messages: { message: MessageType; user: User }[]
    onSend?: () => void
    chatInput?: string
  }

  let { messages, onSend, chatInput = $bindable() }: Props = $props()
</script>

<div class="flex flex-col gap-4">
  <div class="flex flex-col gap-2 p-4 grow">
    {#each messages as message, index (index)}
      <Message message={message.message} user={message.user} />
    {/each}
  </div>
  <div class="flex gap-2 p-4">
    <Input
      bind:value={chatInput}
      onkeydown={(event) => event.key === "Enter" && onSend && onSend()}
    />
    <Button size="icon" variant="secondary" onclick={onSend}>
      <Send />
    </Button>
  </div>
</div>
