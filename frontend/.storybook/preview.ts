import type { Preview } from "@storybook/sveltekit"
import { themes } from "storybook/theming"

const preview: Preview = {
  parameters: {
    docs: { theme: themes.dark },
    backgrounds: { options: { dark: { name: "Dark", value: "#000" } } },
    controls: { matchers: { color: /(background|color)$/i, date: /Date$/i } },
  },
  initialGlobals: { backgrounds: { value: "dark" }, theme: "dark" },
}

export default preview
