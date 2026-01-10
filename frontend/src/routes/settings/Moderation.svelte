<script lang="ts">
  import { Button, buttonVariants } from "$lib/components/ui/button"
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
  import { Textarea } from "$lib/components/ui/textarea"
  import X from "@lucide/svelte/icons/x"
  import { Checkbox } from "$lib/components/ui/checkbox"
  import { Label } from "$lib/components/ui/label"
  import { useModeration } from "$lib/utils.svelte"
  import ShieldQuestionMark from "@lucide/svelte/icons/shield-question-mark"

  let moderation = useModeration()
  const { sources, links, match } = $derived(moderation)
  let words = $derived(moderation.words)
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

<div class="pb-36 flex flex-col gap-2">
  <h2 class="text-xl font-bold">Block custom words</h2>
  <FieldDescription>
    Filter out unwanted content in chat messages from others by specifying a blocked word list or
    use regular expression patterns to fine-tune filtering. These are stored locally in your browser
    and not shared with anyone for privacy and performance reasons.
  </FieldDescription>
  <div class="flex flex-col gap-2 border rounded-md p-4">
    <h3 class="text-lg font-semibold">Filtered words</h3>
    <Textarea bind:value={words.value} />
    <FieldDescription>
      Specify words to filter case-insensitively, separated by commas or new lines. For each word,
      use * or ** as wildcards to match any sequence of characters, ? to match any single character.
      Use \ to escape special characters (\* matches a literal asterisk).
    </FieldDescription>
  </div>

  <h2 class="text-xl font-bold">Links</h2>
  <FieldDescription>Control how links in chat messages are handled.</FieldDescription>
  <div class="flex items-center gap-3">
    <Checkbox id="block-links" bind:checked={links.block} />
    <Label for="block-links">Block chat messages containing links</Label>
  </div>
  <div class="flex items-center gap-3">
    <Checkbox id="warn-links" bind:checked={links.warn} />
    <Label for="warn-links">Warn me when clicking links in messages from others</Label>
  </div>

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
        <InputGroup class="font-mono">
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
          {@const invalid = (() => {
            if (!source) return true
            try {
              new RegExp(source, flags)
              return false
            } catch {
              return true
            }
          })()}

          <InputGroupInput bind:value={sources[index][0]} aria-invalid={invalid} />
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
                  <TooltipContent>This pattern filtered the test input</TooltipContent>
                </Tooltip>
              </InputGroupText>
            </InputGroupAddon>
          {/if}
          {#if invalid}
            <InputGroupAddon align="inline-end">
              <InputGroupText>
                <Tooltip>
                  <TooltipTrigger>
                    <ShieldQuestionMark />
                  </TooltipTrigger>
                  <TooltipContent>This pattern is invalid</TooltipContent>
                </Tooltip>
              </InputGroupText>
            </InputGroupAddon>
          {/if}
        </InputGroup>
        <Tooltip>
          <TooltipTrigger
            class={buttonVariants({ variant: "outline" })}
            onclick={() => sources.splice(index, 1)}
          >
            <X class="text-destructive" />
          </TooltipTrigger>
          <TooltipContent>Remove this pattern</TooltipContent>
        </Tooltip>
      </ButtonGroup>
    {:else}
      <Empty>
        <EmptyHeader>
          <EmptyTitle>No patterns added</EmptyTitle>
          <EmptyDescription
            >Add regular expressions to fine-tune content filtering.</EmptyDescription
          >
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
        <InputGroupInput bind:value={test} aria-invalid={!!(matches && test)} />
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
</div>
