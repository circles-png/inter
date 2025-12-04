<script lang="ts">
  import "../app.css"
  import type { Message } from "../models/message"
    import type { User } from "../models/user"

  interface Props {
    message: Message
    user: User
  }

  const { message, user }: Props = $props()
</script>

<div class="flex gap-2">
  <span class="text-xs text-muted-foreground leading-6">{message.time}</span>
  <p>
    <span style:color={user.colour}>{user.username}:</span>
    {#each message.message as fragment, index (index)}
      {#if fragment.type === "text"}
        <span>{fragment.text}</span>
      {:else if fragment.type === "emote"}
        <img
          class="inline-block"
          src={fragment.url}
          alt={fragment.name}
          style="width: 1.5em; height: 1.5em;"
        />
      {/if}
    {/each}
  </p>
</div>
