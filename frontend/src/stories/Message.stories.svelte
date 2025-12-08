<script module>
  import { defineMeta } from "@storybook/addon-svelte-csf"
  import Message from "./Message.svelte"

  const { Story } = defineMeta({ title: "Atoms/Message", component: Message, tags: ["autodocs"] })
</script>

<Story
  name="Default"
  args={{
    message: { time: "12:34", message: [{ type: "text", text: "Hello, world!" }] },
    user: { id: 1, username: "Viewer", avatar: "", colour: "#aaf", roles: [] },
  }}
/>
