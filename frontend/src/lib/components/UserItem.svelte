<script lang="ts">
  import { resolve } from "$app/paths"
  import Logo from "$lib/components/logo.svelte"
  import { AvatarImage, AvatarFallback, Avatar } from "$lib/components/ui/avatar"
  import { Item, ItemContent, ItemDescription, ItemMedia, ItemTitle } from "$lib/components/ui/item"
  import { server } from "$lib/utils.svelte"
  import type { Snippet } from "svelte"
  import type { User } from "../../models/user"
  import { TooltipTrigger, TooltipContent, Tooltip, TooltipProvider } from "./ui/tooltip"
  import { Button } from "./ui/button"

  const { children, user }: { children: Snippet; user: User | null } = $props()
</script>

{#if user}
  <Button
    href={resolve("/(main)/@[username=user]", { username: user.username })}
    class="min-w-0 p-0"
    variant="ghost"
  >
    {@render inner()}
  </Button>
{:else}
  {@render inner()}
{/if}
{#snippet inner()}
  <Item size="xs" class="flex-nowrap">
    <ItemMedia>
      {#if user}
        <Avatar>
          <AvatarImage src={server.user.avatar(user.username)} alt={user.username} />
          <AvatarFallback><Logo class="fill-muted-foreground size-6" /></AvatarFallback>
        </Avatar>
      {/if}
    </ItemMedia>
    <ItemContent>
      {#if user}
        <TooltipProvider>
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
                {user.displayName || user.username}
              </TooltipContent>
            </Tooltip>
          </ItemTitle>
          {#if user.displayName}
            <ItemDescription>
              <Tooltip>
                <TooltipTrigger>
                  {#snippet child({ props })}
                    <span {...props} class="truncate">@{user.username}</span>
                  {/snippet}
                </TooltipTrigger>
                <TooltipContent>
                  {user.username}
                </TooltipContent>
              </Tooltip>
            </ItemDescription>
          {/if}
        </TooltipProvider>
      {/if}
    </ItemContent>
    {@render children()}
  </Item>
{/snippet}
