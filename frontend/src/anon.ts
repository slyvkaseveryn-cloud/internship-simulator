/** Anonymous browser id: links "opened the site" to a later sign-up in the funnel. */
const KEY = 'is.anon'

export function anonId(): string {
  try {
    let id = localStorage.getItem(KEY)
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem(KEY, id)
    }
    return id
  } catch {
    return 'no-storage'
  }
}
