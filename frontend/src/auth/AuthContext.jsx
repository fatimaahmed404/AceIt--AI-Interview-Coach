import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { authApi } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // On startup, ask the backend who we are (session cookie). Never assume
  // authentication from a client-side flag alone.
  const refresh = useCallback(async () => {
    try {
      const data = await authApi.me()
      setUser(data?.user || null)
    } catch {
      setUser(null)
    }
  }, [])

  useEffect(() => {
    let active = true
    ;(async () => {
      try {
        const data = await authApi.me()
        if (active) setUser(data?.user || null)
      } catch {
        if (active) setUser(null)
      } finally {
        if (active) setLoading(false)
      }
    })()
    return () => { active = false }
  }, [])

  const login = useCallback(async (email, password, remember) => {
    const data = await authApi.login({ email, password, remember })
    setUser(data.user)
    return data.user
  }, [])

  const logout = useCallback(async () => {
    try { await authApi.logout() } catch { /* ignore */ }
    setUser(null)
  }, [])

  const value = { user, loading, isAuthenticated: !!user, login, logout, refresh, setUser }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
