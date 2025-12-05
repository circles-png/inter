import type { User } from "../models/user";

const user = $state<Promise<User | null>>(new Promise(() => { }))

export const context = {
  user,
}
