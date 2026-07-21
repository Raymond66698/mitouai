import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AuthContext = createContext(null)
const API = '/api'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(() => localStorage.getItem('mitouai_token'))

  // 恢复登录状态
  useEffect(() => {
    if (token) {
      fetch(`${API}/users/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data?.id) {
            setUser(data)
            fetchQuota(token).then(q => setUser(prev => ({ ...prev, ...q })))
          } else {
            logout()
          }
        })
        .catch(() => setLoading(false))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token])

  const authFetch = useCallback(async (url, options = {}) => {
    const headers = { ...options.headers, 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    return fetch(`${API}${url}`, { ...options, headers })
  }, [token])

  const fetchQuota = async (t) => {
    try {
      const r = await fetch(`${API}/users/quota`, {
        headers: { Authorization: `Bearer ${t || token}` }
      })
      return r.ok ? r.json() : null
    } catch { return null }
  }

  const login = async (email, password) => {
    const r = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    const data = await r.json()
    if (!r.ok) throw new Error(data.detail || '登录失败')
    localStorage.setItem('mitouai_token', data.access_token)
    setToken(data.access_token)
    setUser(data.user)
    return data
  }

  const register = async (email, password, displayName) => {
    const r = await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName })
    })
    const data = await r.json()
    if (!r.ok) throw new Error(data.detail || '注册失败')
    return data
  }

  const logout = () => {
    localStorage.removeItem('mitouai_token')
    setToken(null)
    setUser(null)
  }

  const refreshUser = async () => {
    const q = await fetchQuota(token)
    setUser(prev => prev ? { ...prev, ...q } : prev)
  }

  return (
    <AuthContext.Provider value={{ user, loading, token, login, register, logout, authFetch, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
