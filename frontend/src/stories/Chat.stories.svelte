<script module>
  import { defineMeta } from "@storybook/addon-svelte-csf"
  import Chat from "./Chat.svelte"

  const { Story } = defineMeta({
    title: "Components/Chat",
    component: Chat,
    argTypes: { colour: { control: "color" } },
  })
</script>

<Story
  name="Default"
  args={{
    messages: [
      {
        user: { username: "A", colour: "#aaf" },
        message: { time: "12:34", message: [{ type: "text", text: "Hello, world!" }] },
      },
      {
        user: { username: "B", colour: "#aaf" },
        message: { time: "12:34", message: [{ type: "text", text: "Hello, world!" }] },
      },
      {
        user: { username: "C", colour: "#aaf" },
        message: { time: "12:35", message: [{ type: "text", text: "Hello, world!" }] },
      },
    ],
  }}
/>
