export type Emote = { name: string; url: string; zeroWidth: boolean }
export type Fragment =
  | ({ type: "emote" } & Emote)
  | { type: "emote-stack"; emotes: Emote[] }
  | { type: "text"; text: string }
export type Message = { time: Date; fragments: Fragment[]; username: string; colour: number }
