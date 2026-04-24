export type Emote = { name: string; url: string; zeroWidth: boolean }
export type Fragment =
  | ({ type: "emote" } & Emote)
  | { type: "emote-stack"; emotes: Emote[] }
  | { type: "text"; text: string }
export type Message =
  | { type: "system"; text: string }
  | {
      type: "message"
      time: Date
      fragments: Fragment[]
      username: string
      colour: number
      replying: null | MessageId
      id: MessageId
      filtered: boolean
      roles: Promise<{ id: number; name: string }[]>
    }
export type MessageId = string & { readonly __brand: unique symbol }
