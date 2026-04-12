import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import {
  clearAuthSession,
  getDashboardPath,
  getPendingSignupAuth,
  isPhoneVerified,
  loadAuthSession,
  saveAuthSession,
  setPhoneVerified,
} from '@/shared/lib/auth.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => loadAuthSession())
  const [phoneVerified, setPhoneVerifiedState] = useState(() => isPhoneVerified())

  useEffect(() => {
    const onStorage = () => {
      setSession(loadAuthSession())
      setPhoneVerifiedState(isPhoneVerified())
    }

    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const login = useCallback((rawSession, options = {}) => {
    const saved = saveAuthSession(rawSession)
    setSession(saved)

    if (typeof options.phoneVerified === 'boolean') {
      setPhoneVerified(options.phoneVerified)
      setPhoneVerifiedState(options.phoneVerified)
    }

    return saved
  }, [])

  const completePhoneVerification = useCallback(() => {
    setPhoneVerified(true)
    setPhoneVerifiedState(true)

    const pending = getPendingSignupAuth()
    if (pending?.userId && pending?.role) {
      const saved = saveAuthSession(pending)
      setSession(saved)
    }
  }, [])

  const logout = useCallback(() => {
    clearAuthSession()
    setSession(null)
    setPhoneVerifiedState(false)
  }, [])

  const value = useMemo(() => ({
    session,
    userId: session?.userId || null,
    role: session?.role || null,
    fullName: session?.fullName || '',
    isAuthenticated: Boolean(session?.userId),
    phoneVerified,
    login,
    logout,
    completePhoneVerification,
    getDashboardPath,
  }), [session, phoneVerified, login, logout, completePhoneVerification])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}