import type { User } from "../models/user"

export const userContext = $state<{ user: User | null }>({
  user: null
})
export const userUpdateContext = $state<{ userUpdate: Promise<bool> | null }>({ userUpdate: null })
