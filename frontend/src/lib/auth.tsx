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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Restore session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('auth_token')
    if (stored) {
      try {
        // Decode JWT payload (no signature verification needed client-side)
        const payload = JSON.parse(atob(stored.split('.')[1]))
        if (payload.exp * 1000 > Date.now()) {
          api.setToken(stored)
          setToken(stored)
          // Fetch current user profile
          api.getMe().then(profile => {
            setUser(profile as AuthUser)
          }).catch(() => {
            localStorage.removeItem('auth_token')
            api.clearToken()
          }).finally(() => setIsLoading(false))
        } else {
          localStorage.removeItem('auth_token')
          setIsLoading(false)
        }
      } catch {
        localStorage.removeItem('auth_token')
        setIsLoading(false)
      }
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = async (email: string, password: string): Promise<AuthUser> => {
    const data = await api.login(email, password)
    localStorage.setItem('auth_token', data.access_token)
    api.setToken(data.access_token)
    setToken(data.access_token)
    const profile = await api.getMe() as AuthUser
    setUser(profile)
    return profile
  }

  const register = async (email: string, password: string, adminKey?: string): Promise<AuthUser> => {
    const data = await api.register(email, password, adminKey)
    localStorage.setItem('auth_token', data.access_token)
    api.setToken(data.access_token)
    setToken(data.access_token)
    const profile = await api.getMe() as AuthUser
    setUser(profile)
    return profile
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
