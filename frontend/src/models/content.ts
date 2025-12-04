import type { User } from "./user"

export type Content = {
  creator: User
  title: string
  description: string
  game: string
  viewerCount: number
  duration: string
}
