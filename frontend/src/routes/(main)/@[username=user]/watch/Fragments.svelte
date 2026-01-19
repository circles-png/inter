<script lang="ts">
  import { Button, buttonVariants } from "$lib/components/ui/button"
  import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
  } from "$lib/components/ui/dialog"
  import { TooltipTrigger, TooltipContent, Tooltip } from "$lib/components/ui/tooltip"
  import SquareArrowOutUpRight from "@lucide/svelte/icons/square-arrow-out-up-right"
  import { cn } from "tailwind-variants"
  import type { Fragment } from "../../../../models/message"
  import { isURL, useModeration } from "$lib/utils.svelte"

  const { fragments }: { fragments: Fragment[] } = $props()
  const moderation = useModeration()
</script>

{#each fragments as fragment, index (index)}
  {#if fragment.type === "text"}
    {#if isURL(fragment.text)}
      {#if moderation.links.warn}
        <Dialog>
          <DialogTrigger class={cn(buttonVariants({ variant: "link", size: "sm" }), "p-0 h-auto")}>
            {fragment.text}
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Are you sure you want to visit this external link?</DialogTitle>
              <DialogDescription class="flex flex-col">
                <code>{fragment.text}</code>
                <span>Make sure you trust the link before proceeding.</span>
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <DialogClose>
                {#snippet child({ props })}
                  <Button
                    variant="destructive"
                    href={fragment.text}
                    target="_blank"
                    rel="noopener noreferrer"
                    {...props}
                  >
                    <SquareArrowOutUpRight />
                    Open
                  </Button>
                {/snippet}
              </DialogClose>
              <DialogClose class={buttonVariants({ variant: "default" })}>Cancel</DialogClose>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      {:else}
        <Button
          href={fragment.text}
          target="_blank"
          rel="noopener noreferer"
          variant="link"
          size="sm"
          class="p-0 h-auto"
        >
          {fragment.text}
        </Button>
      {/if}
    {:else}
      <span>{fragment.text}</span>
    {/if}
  {:else if fragment.type === "emote"}
    <Tooltip>
      <TooltipTrigger class="inline-flex items-center">
        <img class="inline-block h-5" src={fragment.url} alt={fragment.name} />
      </TooltipTrigger>
      <TooltipContent class="flex flex-col items-center">
        <img class="inline-block h-10" src={fragment.url} alt={fragment.name} />
        {fragment.name}
      </TooltipContent>
    </Tooltip>
  {:else if fragment.type === "emote-stack"}
    <Tooltip>
      <TooltipTrigger class="inline-flex items-center">
        <span class="inline-grid place-items-center h-6">
          {#each fragment.emotes as emote, index (index)}
            <img
              class="inline-block h-5 col-start-1 row-start-1"
              src={emote.url}
              alt={emote.name}
            />
          {/each}
        </span>
      </TooltipTrigger>
      <TooltipContent class="flex flex-col items-center">
        <div class="-rotate-x-20 rotate-y-40 relative h-30 w-60 perspective-distant transform-3d">
          {#each fragment.emotes as emote, index (index)}
            <img
              class="h-10 absolute w-30 object-contain"
              src={emote.url}
              alt={emote.name}
              style:transform={`translateZ(${index * 40}px)`}
            />
          {/each}
        </div>
        {#each fragment.emotes as emote, index (index)}
          <span>{emote.name}</span>
        {/each}
      </TooltipContent>
    </Tooltip>
  {/if}
{/each}
