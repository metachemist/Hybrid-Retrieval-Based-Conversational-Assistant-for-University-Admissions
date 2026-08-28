'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { api } from './api'

interface AuthUser {
  id: string
  email: string
  role: 'user' | 'admin'
}

interface AuthContextType {
  user: AuthUser | null
  token: string | null
  login: (email: string, password: string) => Promise<AuthUser>
  register: (email: string, password: string, adminKey?: string) => Promise<AuthUser>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

/**
 * Decode the JWT payload (sub, email, role, exp) with no signature check —
 * the server re-verifies on every authenticated request. Returns null if the
 * token is malformed or expired. This is what lets sign-in skip a follow-up
 * /auth/me round trip: the token already carries everything the UI needs.
 */
function userFromToken(token: string): AuthUser | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (!payload.exp || payload.exp * 1000 <= Date.now()) return null
    return {
      id: payload.sub,
      email: payload.email ?? '',
      role: payload.role === 'admin' ? 'admin' : 'user',
    }
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Restore the session from localStorage on mount — purely local, no network.
  useEffect(() => {
    const stored = localStorage.getItem('auth_token')
    const restored = stored ? userFromToken(stored) : null
    if (stored && restored) {
      api.setToken(stored)
      setToken(stored)
      setUser(restored)
    } else if (stored) {
      localStorage.removeItem('auth_token')
    }
    setIsLoading(false)
  }, [])

  const persist = (accessToken: string): AuthUser => {
    const profile = userFromToken(accessToken)
    if (!profile) throw new Error('Received an invalid token')
    localStorage.setItem('auth_token', accessToken)
    api.setToken(accessToken)
    setToken(accessToken)
    setUser(profile)
    return profile
  }

  const login = async (email: string, password: string): Promise<AuthUser> => {
    const data = await api.login(email, password)
    return persist(data.access_token)
  }

  const register = async (email: string, password: string, adminKey?: string): Promise<AuthUser> => {
    const data = await api.register(email, password, adminKey)
    return persist(data.access_token)
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    api.clearToken()
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
