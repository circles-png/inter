import type { User } from "../models/user";

function create<T>(name, initial: T) {
  let state = $state<T>(initial)
  return {
    get() {
      return state
    },
    set(value: T) {
      state = value
    },
  }
}

export default Object.defineProperties({} as { user: Promise<User | null> }, {
  user: create(new Promise(() => { }))
})
