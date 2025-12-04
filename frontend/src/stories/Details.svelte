<script lang="ts">
  import "../app.css"
  import Avatar from "$lib/components/ui/avatar/avatar.svelte"
  import AvatarImage from "$lib/components/ui/avatar/avatar-image.svelte"
  import type { Content } from "../models/content"
  import { AvatarFallback } from "$lib/components/ui/avatar"
  import User from "@lucide/svelte/icons/user"
  import Timer from "@lucide/svelte/icons/timer"

  interface Props {
    content: Content
  }

  const { content }: Props = $props()
</script>

<div class="flex justify-between p-4">
  <div class="flex gap-4">
    <Avatar class="size-16">
      <AvatarImage src={content.creator.avatar} />
      <AvatarFallback class="bg-muted" />
    </Avatar>
    <div class="flex flex-col">
      <div class="text-2xl font-bold">{content.title}</div>
      <div>{content.description}</div>
      <div class="text-muted-foreground">{content.game}</div>
    </div>
  </div>
  <div class="flex flex-col text-red-400 font-mono">
    <div class="flex gap-2">
      <User />
      {content.viewerCount}
    </div>
    <div class="flex gap-2">
      <Timer />
      {content.duration}
    </div>
  </div>
</div>
