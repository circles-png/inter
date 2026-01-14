export type Poll = {
  id: string
  question: string
  options: { text: string; percent?: number }[]
  duration: number
  start: number
}
