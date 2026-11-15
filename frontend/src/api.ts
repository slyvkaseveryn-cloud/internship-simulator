import { getIdToken } from './auth'

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getIdToken()
  const r = await fetch(`/api${path}`, {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  })
  if (!r.ok) throw new Error(`API ${r.status}`)
  return r.json()
}
