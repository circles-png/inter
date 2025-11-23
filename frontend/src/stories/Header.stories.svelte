<script module>
  import { defineMeta } from "@storybook/addon-svelte-csf"
  import Header from "./Header.svelte"
  import { fn } from "storybook/test"

  const { Story } = defineMeta({
    title: "Components/Header",
    component: Header,
    tags: ["autodocs"],
    parameters: { layout: "fullscreen" },
    args: { onLogin: fn(), onLogout: fn(), onCreateAccount: fn() },
  })
</script>

<Story
  name="Logged In"
  args={{ user: { id: 1, username: "User", avatar: "http://picsum.photos/200" } }}
/>

<Story name="Logged Out" />
