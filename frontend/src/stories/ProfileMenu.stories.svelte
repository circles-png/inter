<script module>
  import { defineMeta } from "@storybook/addon-svelte-csf"
  import ProfileMenu from "./ProfileMenu.svelte"
  import { fn } from "storybook/test"

  const { Story } = defineMeta({
    title: "Atoms/ProfileMenu",
    component: ProfileMenu,
    tags: ["autodocs"],
    argTypes: { size: { control: { type: "select" }, options: ["small", "medium", "large"] } },
  })
</script>

<Story
  name="Default"
  args={{ user: { id: 1, username: "User", avatar: "http://picsum.photos/200" } }}
/>
