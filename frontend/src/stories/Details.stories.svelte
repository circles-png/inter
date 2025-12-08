<script module>
  import { defineMeta } from "@storybook/addon-svelte-csf"
  import Details from "./Details.svelte"

  const { Story } = defineMeta({
    title: "Components/Details",
    component: Details,
    argTypes: { colour: { control: "color" } },
  })
</script>

<Story
  name="Default"
  args={{
    content: {
      creator: {
        id: 1,
        username: "Viewer",
        avatar: "http://picsum.photos/200",
        colour: "#aaf",
        roles: [],
      },
      title: "Sample Stream",
      description: "This is a sample stream description.",
      game: "Sample Game",
      viewerCount: 1234,
      duration: "12:34:56",
    },
  }}
/>
