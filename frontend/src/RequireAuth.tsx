import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './useAuth'

export default function RequireAuth({ children }: { children: ReactNode }) {
  const { signedIn } = useAuth()
  const loc = useLocation()
  if (!signedIn) return <Navigate to={`/signin?next=${encodeURIComponent(loc.pathname)}`} replace />
  return <>{children}</>
}
