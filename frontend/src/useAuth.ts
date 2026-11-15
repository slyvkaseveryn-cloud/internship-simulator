import { useEffect, useState } from 'react'
import { currentClaims, isSignedIn } from './auth'

export function useAuth() {
  const [state, setState] = useState(() => ({ signedIn: isSignedIn(), claims: currentClaims() }))
  useEffect(() => {
    const update = () => setState({ signedIn: isSignedIn(), claims: currentClaims() })
    window.addEventListener('auth-changed', update)
    window.addEventListener('storage', update)
    return () => {
      window.removeEventListener('auth-changed', update)
      window.removeEventListener('storage', update)
    }
  }, [])
  return state
}
