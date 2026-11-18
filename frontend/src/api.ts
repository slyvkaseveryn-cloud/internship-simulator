import { anonId } from './anon'
import { getIdToken } from './auth'

export class ApiError extends Error {
  status: number
  code: string
  constructor(status: number, code: string) {
    super(`API ${status} ${code}`)
    this.status = status
    this.code = code
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getIdToken()
  const r = await fetch(`/api${path}`, {
    ...init,
    headers: {
      'content-type': 'application/json',
      'x-anon-id': anonId(),
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new ApiError(r.status, data.error ?? 'unknown')
  return data as T
}

export const post = <T>(path: string, body: unknown) => api<T>(path, { method: 'POST', body: JSON.stringify(body) })
export const put = <T>(path: string, body: unknown) => api<T>(path, { method: 'PUT', body: JSON.stringify(body) })

/** Fire-and-forget event; never breaks the page. */
export function track(event: string, caseId?: string, value?: string) {
  post('/events', { event, caseId, value }).catch(() => {})
}
