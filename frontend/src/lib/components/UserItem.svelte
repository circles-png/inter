<script lang="ts">
  import { resolve } from "$app/paths"
  import Logo from "$lib/components/logo.svelte"
  import { AvatarImage, AvatarFallback, Avatar } from "$lib/components/ui/avatar"
  import { Item, ItemContent, ItemMedia, ItemTitle } from "$lib/components/ui/item"
  import { server } from "$lib/utils.svelte"
  import type { Snippet } from "svelte"
  import type { User } from "../../models/user"
  import { TooltipTrigger, TooltipContent, Tooltip } from "./ui/tooltip"
  import { Button } from "./ui/button"

  const { children, user }: { children: Snippet; user: User | null } = $props()
</script>

<Item size="xs" class="flex-nowrap grow justify-end">
  {#if user}
    <Button
      href={resolve("/(main)/@[username=user]", { username: user.username })}
      class="flex-1 p-0.5"
      variant="ghost"
    >
      <ItemMedia>
        <Avatar>
          <AvatarImage src={server.user.avatar(user.username)} alt={user.username} />
          <AvatarFallback><Logo class="fill-muted-foreground size-6" /></AvatarFallback>
        </Avatar>
      </ItemMedia>
      <ItemContent>
        <ItemTitle>
          <Tooltip>
            <TooltipTrigger>
              {#snippet child({ props })}
                <span {...props} class="truncate">
                  {user.displayName || user.username}
                </span>
              {/snippet}
            </TooltipTrigger>
            <TooltipContent>
              @{user.username}
            </TooltipContent>
          </Tooltip>
        </ItemTitle>
      </ItemContent>
    </Button>
  {/if}
  {@render children()}
</Item>
