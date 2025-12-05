export function match(username) {
  return /^@[a-z0-9_]{4,32}$/.test(username);
}
