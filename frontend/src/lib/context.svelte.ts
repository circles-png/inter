import type { User } from "../models/user"

export const userContext = $state<{ user: Promise<User | null> }>({ user: new Promise(() => {}) })
export const userUpdateContext = $state<{ userUpdate: Promise<void> | null }>({ userUpdate: null })
