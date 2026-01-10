<script module>
  class Moderation {
    sources: [string, string][] = $state([])
    regexes = $derived(
      this.sources.flatMap(([source, flags]) => {
        try {
          return [new RegExp(source, flags)]
        } catch {
          return []
        }
      }),
    )
    constructor() {
      const item = localStorage.getItem("sources")
      if (!item) return
      this.sources = JSON.parse(item)
      $effect(() => {
        localStorage.setItem("sources", JSON.stringify(this.sources))
      })
    }
  }

  function useModeration() {
    const moderation = new Moderation()
    let match = (input: string) =>
      moderation.regexes.some((regex) => !regex.test("") && regex.exec(input))
    return { sources: moderation.sources, match }
  }
</script>

<script lang="ts">
  import { Button } from "$lib/components/ui/button"
  import { ButtonGroup } from "$lib/components/ui/button-group"
  import {
    DropdownMenu,
    DropdownMenuCheckboxItem,
    DropdownMenuContent,
    DropdownMenuGroup,
    DropdownMenuLabel,
    DropdownMenuTrigger,
  } from "$lib/components/ui/dropdown-menu"
  import {
    Empty,
    EmptyContent,
    EmptyDescription,
    EmptyHeader,
    EmptyTitle,
  } from "$lib/components/ui/empty"
  import { FieldDescription } from "$lib/components/ui/field"
  import {
    InputGroup,
    InputGroupAddon,
    InputGroupText,
    InputGroupButton,
    InputGroupInput,
  } from "$lib/components/ui/input-group"
  import { Tooltip, TooltipContent, TooltipTrigger } from "$lib/components/ui/tooltip"
  import Plus from "@lucide/svelte/icons/plus"
  import { SIDEBAR_WIDTH } from "$lib/components/ui/sidebar/constants"
  import { useSidebar } from "$lib/components/ui/sidebar"
  import { IsMobile } from "$lib/hooks/is-mobile.svelte"
  import { cn } from "$lib/utils"
  import MessageSquareWarning from "@lucide/svelte/icons/message-square-warning"

  const { sources, match } = useModeration()
  let test = $state("")
  const availableFlags = [
    {
      name: "Multi line",
      letter: "m",
      description: "Make ^ and $ match the start and end of line",
    },
    { name: "Ignore case", letter: "i", description: "Match case-insensitively" },
    { name: "Unicode", letter: "u", description: "Match with full unicode support" },
    { name: "Vnicode", letter: "v", description: "Enable all unicode and character set features" },
    { name: "Single line", letter: "s", description: "Dot matches newline" },
  ]
  const addPattern = () => {
    sources.push(["", "im"])
  }
  let isMobile = new IsMobile()
  const matches = $derived(match(test))
</script>

<h2 class="text-xl font-bold">Wordlist</h2>
<h2 class="text-xl font-bold">Links</h2>

<h2 class="text-xl font-bold">Advanced</h2>
<div class="flex flex-col gap-2 border rounded-md p-4">
  <div class="flex gap-2 justify-between">
    <h3 class="text-lg font-semibold">Regular expression patterns</h3>
    <Button variant="outline" size="sm" onclick={addPattern}>
      <Plus />
      Add a pattern
    </Button>
  </div>
  {#each sources as [source, flags], index (index)}
    <ButtonGroup>
      <InputGroup>
        <InputGroupAddon><InputGroupText>/</InputGroupText></InputGroupAddon>
        <InputGroupAddon align="inline-end">
          <DropdownMenu>
            <DropdownMenuTrigger>
              {#snippet child({ props: outerProps })}
                <Tooltip>
                  <TooltipTrigger>
                    {#snippet child({ props })}
                      <InputGroupButton {...props} {...outerProps}>
                        /{flags}
                      </InputGroupButton>
                    {/snippet}
                  </TooltipTrigger>
                  <TooltipContent>Edit regex flags</TooltipContent>
                </Tooltip>
              {/snippet}
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuGroup>
                <DropdownMenuLabel>Flags</DropdownMenuLabel>
                {#each availableFlags as { name, letter, description } (letter)}
                  <DropdownMenuCheckboxItem
                    bind:checked={
                      () => flags.includes(letter),
                      (enabled) => {
                        let nextFlags = flags
                        if (nextFlags.includes("u") && letter === "v" && enabled) {
                          nextFlags = nextFlags.replace("u", "")
                        }
                        if (nextFlags.includes("v") && letter === "u" && enabled) {
                          nextFlags = nextFlags.replace("v", "")
                        }
                        if (nextFlags.includes(letter) && !enabled) {
                          nextFlags = nextFlags.replace(letter, "")
                        } else if (!nextFlags.includes(letter) && enabled) {
                          nextFlags += letter
                        }
                        sources[index] = [sources[index][0], new RegExp("", nextFlags).flags]
                      }
                    }
                  >
                    {name}
                    <span class="text-muted-foreground">{description}</span>
                  </DropdownMenuCheckboxItem>
                {/each}
              </DropdownMenuGroup>
            </DropdownMenuContent>
          </DropdownMenu>
        </InputGroupAddon>
        {#if (() => {
          try {
            const regex = new RegExp(source, flags)
            return !regex.test("") && regex.test(test)
          } catch {
            return false
          }
        })()}
          <InputGroupAddon align="inline-end">
            <InputGroupText>
              <Tooltip>
                <TooltipTrigger>
                  <MessageSquareWarning />
                </TooltipTrigger>
                <TooltipContent>This pattern matches the test input</TooltipContent>
              </Tooltip>
            </InputGroupText>
          </InputGroupAddon>
        {/if}
        <InputGroupInput
          bind:value={sources[index][0]}
          aria-invalid={(() => {
            if (!source) return true
            try {
              new RegExp(source, flags)
              return false
            } catch {
              return true
            }
          })()}
          class="font-mono"
        />
      </InputGroup>
    </ButtonGroup>
  {:else}
    <Empty>
      <EmptyHeader>
        <EmptyTitle>No patterns added</EmptyTitle>
        <EmptyDescription>Add regular expressions to fine-tune content filtering.</EmptyDescription>
      </EmptyHeader>
      <EmptyContent>
        <Button onclick={addPattern}>
          <Plus />
          Add a pattern
        </Button>
      </EmptyContent>
    </Empty>
  {/each}
  <FieldDescription>
    Specify regular expressions for filtering content. These are applied disjunctively (content
    matching any of the expressions will be filtered).
  </FieldDescription>
</div>

<div
  class="fixed bottom-0 right-0 p-2 transition-[left]"
  style={`left: ${useSidebar().open && !isMobile.current ? SIDEBAR_WIDTH : "0px"}`}
>
  <div class="flex flex-col gap-2 p-4 bg-background border rounded-md">
    <h3 class="text-2xl font-semibold">Test filters</h3>
    <InputGroup class={cn(!matches && test && "ring-green-400/40!")}>
      <InputGroupInput bind:value={test} aria-invalid={matches} />
      <InputGroupAddon align="inline-end">
        <InputGroupText>
          {#if test}
            {#if matches}
              <div class="text-destructive">Filtered</div>
            {:else}
              <div class="text-green-400">Allowed</div>
            {/if}
          {/if}
        </InputGroupText>
      </InputGroupAddon>
    </InputGroup>
  </div>
</div>
