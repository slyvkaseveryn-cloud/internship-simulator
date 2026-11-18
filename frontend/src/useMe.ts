import { useCallback, useEffect, useState } from 'react'
import { api } from './api'

export type Me = { email: string; name: string; profession: string | null; isReviewer: boolean }

let cached: Me | null = null
window.addEventListener('auth-changed', () => {
  cached = null
})

export function useMe() {
  const [me, setMe] = useState<Me | null>(cached)
  const [error, setError] = useState(false)
  const reload = useCallback(() => {
    api<Me>('/me').then((m) => {
      cached = m
      setMe(m)
    }).catch(() => setError(true))
  }, [])
  useEffect(() => {
    if (!cached) reload()
  }, [reload])
  return { me, error, reload, setMe: (m: Me) => { cached = m; setMe(m) } }
}
