import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { canAccessPath } from './roles'

export type MockUser = {
  name: string
  role: 'Client' | 'Volunteer' | 'Warehouse Staff' | 'Warehouse Manager' | 'Director'
  enrollmentStatus: 'Active' | 'Pending'
}

type AuthContextValue = {
  user: MockUser | null
  signIn: (email: string, password: string) => { ok: boolean; reason?: 'invalid' | 'inactive' }
  signOut: () => void
}

const demoUser: MockUser = {
  name: 'Jordan Lee',
  role: 'Client',
  enrollmentStatus: 'Active',
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<MockUser | null>(() =>
    window.sessionStorage.getItem('nest-demo-user') ? demoUser : null,
  )

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      signIn: (email, password) => {
        if (email === 'demo@example.test' && password === 'welcome') {
          window.sessionStorage.setItem('nest-demo-user', 'true')
          setUser(demoUser)
          return { ok: true }
        }
        if (email === 'pending@example.test' && password === 'welcome') {
          return { ok: false, reason: 'inactive' }
        }
        return { ok: false, reason: 'invalid' }
      },
      signOut: () => {
        window.sessionStorage.removeItem('nest-demo-user')
        setUser(null)
      },
    }),
    [user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}

export function ProtectedRoute() {
  const { user } = useAuth()
  const location = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  return canAccessPath(user.role, location.pathname) || location.pathname === '/unauthorized' ? <Outlet /> : <Navigate to="/unauthorized" replace />
}
