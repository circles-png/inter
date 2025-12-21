<script lang="ts">
  import Logo from "$lib/components/logo.svelte"
  import { AvatarImage, AvatarFallback, Avatar } from "$lib/components/ui/avatar"
  import { Item, ItemContent, ItemDescription, ItemMedia, ItemTitle } from "$lib/components/ui/item"
  import { userContext } from "$lib/context.svelte"
  import "../../app.css"
  import { TooltipTrigger, TooltipContent, Tooltip, TooltipProvider } from "./ui/tooltip"

  const { children } = $props()
  const user = $derived(userContext.user)
</script>

{#if user}
  <Item size="xs" class="flex-nowrap grow min-w-0">
    <ItemMedia>
      <Avatar class="*:rounded-lg size-8">
        <AvatarImage src={user.avatar} alt="User avatar" />
        <AvatarFallback><Logo class="fill-muted-foreground size-6" /></AvatarFallback>
      </Avatar>
    </ItemMedia>
    <ItemContent class="gap-0 min-w-0">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger>
            {#snippet child({ props })}
              <ItemTitle class="truncate block w-auto" {...props}>
                {user.displayName || user.username}
              </ItemTitle>
            {/snippet}
          </TooltipTrigger>
          <TooltipContent>
            {user.displayName || user.username}
          </TooltipContent>
        </Tooltip>
        {#if user.displayName}
          <Tooltip>
            <TooltipTrigger>
              {#snippet child({ props })}
                <ItemDescription class="truncate block w-auto" {...props}>
                  @{user.username}
                </ItemDescription>
              {/snippet}
            </TooltipTrigger>
            <TooltipContent>
              {user.username}
            </TooltipContent>
          </Tooltip>
        {/if}
      </TooltipProvider>
    </ItemContent>
    {@render children()}
  </Item>
{/if}
