<script lang="ts">
  import Logs from "@lucide/svelte/icons/logs"
  import { Sheet, SheetContent, SheetHeader, SheetTitle } from "$lib/components/ui/sheet"
  import type { Message } from "../../../../models/message"
  import Reply from "@lucide/svelte/icons/reply"
  import Ellipsis from "@lucide/svelte/icons/ellipsis-vertical"
  import Fragments from "./Fragments.svelte"
  import { colours, server } from "$lib/utils.svelte"
  import type { User } from "../../../../models/user"
  import { HoverCard, HoverCardContent, HoverCardTrigger } from "$lib/components/ui/hover-card"
  import { Button, buttonVariants } from "$lib/components/ui/button"
  import { Avatar, AvatarFallback, AvatarImage } from "$lib/components/ui/avatar"
  import { resolve } from "$app/paths"
  import { ButtonGroup } from "$lib/components/ui/button-group"
  import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
  } from "$lib/components/ui/dropdown-menu"
  import ChatMessages from "./ChatMessages.svelte"
  import ShieldBan from "@lucide/svelte/icons/shield-ban"
  import ShieldOff from "@lucide/svelte/icons/shield-off"

  let {
    messages = $bindable(),
    user,
    replying = $bindable(),
    chatInput,
    inChatLogs = false,
    showTimes,
    username,
  }: {
    messages: Message[]
    user: User | null
    replying: Extract<Message, { type: "message" }> | null
    chatInput: HTMLInputElement | null
    inChatLogs?: boolean
    showTimes: boolean
    username: string
  } = $props()
  let messagesContainer: HTMLDivElement
  let chatLogs: string | null = $state(null)

  const m = $derived(messages.filter((message) => message !== undefined))

  $effect(() => {
    if (messages.length) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight
    }
  })
</script>

<div class="flex flex-col grow overflow-y-auto min-h-0" bind:this={messagesContainer}>
  {#each m as message, index (message.type == "message" ? message.id : index)}
    {@const { fragments } = message}
    <div class="flex flex-col">
      {#if message.type == "message" && message.replying}
        {@const replyingTo = m.find(
          (other): other is Extract<Message, { type: "message" }> =>
            other.type == "message" && message.replying == other.id,
        )}
        {#if replyingTo}
          <div class="px-4">
            <div class="text-xs [--spacing:0.2em] text-muted-foreground flex gap-2 items-center">
              <Reply class="size-6" />
              <p>
                Replying to
                <span style="color: {colours[replyingTo.colour]}">{replyingTo.username}</span>:
                <Fragments fragments={replyingTo.fragments} />
              </p>
            </div>
          </div>
        {/if}
      {/if}
      <div
        class={[
          "flex gap-2 items-center px-4 group transition",
          user
            && fragments.some(
              (fragment) => fragment.type == "text" && fragment.text == user?.username,
            )
            && "bg-red-500/20 border-l-4 border-red-500",
          message.type == "message"
            && message.id === replying?.id
            && "border-l-4 border-green-500 bg-green-500/20",
          message.type == "message" && message.filtered && "opacity-50 has-hover:opacity-100",
          message.type == "system" && "text-xs text-muted-foreground *:[--spacing:0.2em]",
        ]}
      >
        {#if message.type == "message" && showTimes}
          <span class="text-xs text-muted-foreground">
            {message.time.toLocaleTimeString()}
          </span>
        {/if}
        <p class="wrap-anywhere grow">
          {#if message.type === "message"}
            {#await server.user
              .user(message.username)
              .then((user) => user.displayName) then displayName}
              <HoverCard>
                <HoverCardTrigger
                  style="color: {colours[message.colour]}"
                  class="cursor-pointer hover:underline"
                  onclick={() =>
                    (chatInput!.value += `${chatInput!.value.trimEnd() == chatInput!.value ? " " : ""}${message.username} `)}
                >
                  {message.username}:
                </HoverCardTrigger>
                <HoverCardContent class="p-0">
                  <Button
                    href={resolve("/(main)/@[username=user]", { username: message.username })}
                    class="h-auto p-4 w-full"
                    variant="ghost"
                  >
                    <Avatar class="size-12">
                      <AvatarImage
                        src={server.user.avatar(message.username)}
                        alt={message.username}
                      />
                      <AvatarFallback class="bg-muted" />
                    </Avatar>
                    <div class="flex flex-col grow">
                      <div class="font-bold">
                        {displayName || `@${message.username}`}
                      </div>
                      {#if displayName}
                        <div class="text-sm text-muted-foreground">@{message.username}</div>
                      {/if}
                    </div>
                  </Button>
                </HoverCardContent>
              </HoverCard>
            {/await}
          {/if}
          {#if message.type === "system" || !message.filtered}
            <Fragments {fragments} />
          {:else}
            <span class="text-muted-foreground">
              <Button
                variant="ghost"
                size="sm"
                class="text-xs p-1 h-auto peer"
                onclick={() => (message.filtered = false)}
              >
                Show filtered message
              </Button>
            </span>
          {/if}
        </p>
        {#if message.type === "message"}
          {@const reply = () => {
            replying = message
            chatInput?.focus()
          }}
          <ButtonGroup
            class="flex opacity-0 scale-90 group-hover:opacity-100 group-hover:scale-100 transition has-focus-visible:opacity-100 has-focus-visible:scale-100 has-data-[state=open]:opacity-100 has-data-[state=open]:scale-100"
          >
            <Button
              variant="ghost"
              size="sm"
              class="h-6 w-6 text-green-300 hover:text-green-500 hover:bg-green-950/50!"
              onclick={reply}
            >
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
                    <span class="text-green-400">Reply</span> to {message.username}
                  </p>
                </DropdownMenuItem>
                {#if !inChatLogs}
                  <DropdownMenuItem onclick={() => (chatLogs = message.username)}>
                    <Logs />
                    See chat logs
                  </DropdownMenuItem>
                {/if}
              </DropdownMenuContent>
            </DropdownMenu>
          </ButtonGroup>
        {/if}
      </div>
    </div>
  {/each}
</div>

{#if !inChatLogs}
  <Sheet open={!!chatLogs} onOpenChange={(open) => !open && (chatLogs = null)}>
    <SheetContent>
      <SheetHeader>
        <SheetTitle>
          Chat logs for {chatLogs}
        </SheetTitle>
        {#if chatLogs != username && user?.username == username}
          <span class="text-sm text-muted-foreground">Moderate user</span>
          <ButtonGroup>
            <ButtonGroup>
              <Button
                variant="outline"
                onclick={async () => chatLogs && server.user.moderate(chatLogs, undefined)}
                size="sm"
              >
                <ShieldOff />
              </Button>
            </ButtonGroup>
            <ButtonGroup>
              {#each [["30s", 30], ["1m", 60], ["5m", 5 * 60], ["30m", 30 * 60], ["1h", 60 * 60], ["1d", 60 * 60 * 24]] as const as [label, duration] (label)}
                <Button
                  variant="outline"
                  onclick={async () => chatLogs && server.user.moderate(chatLogs, duration)}
                  size="sm"
                  class="text-xs"
                >
                  {label}
                </Button>
              {/each}
            </ButtonGroup>
            <ButtonGroup>
              <Button
                variant="outline"
                onclick={async () => chatLogs && server.user.moderate(chatLogs, null)}
                size="sm"
              >
                <ShieldBan />
              </Button>
            </ButtonGroup>
          </ButtonGroup>
        {/if}
      </SheetHeader>
      <ChatMessages
        {user}
        bind:replying
        {chatInput}
        messages={messages.filter(
          (other) => other.type === "message" && other.username == chatLogs,
        )}
        inChatLogs
        {showTimes}
        {username}
      />
    </SheetContent>
  </Sheet>
{/if}
