export type Fragment = ({ type: Emote } & Emote) | { type: "text"; text: string; name: string }
export type Message = { time: string; message: Fragment[] }
