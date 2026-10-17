import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

function Loader({ label = 'Loading…' }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      gap: 10, minHeight: '60vh', color: 'var(--color-text-secondary)', fontSize: 14,
    }}>
      <span style={{
        width: 16, height: 16, border: '2px solid #534AB7', borderTopColor: 'transparent',
        borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite',
      }} />
      {label}
      <style>{`@keyframes spin {to {transform: rotate(360deg)}}`}</style>
    </div>
  )
}

/** Requires authentication. Remembers where the user was headed. */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()
  if (loading) return <Loader />
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  }
  return children
}

/** Guest-only (login/signup/etc). Sends authenticated users to the app. */
export function GuestRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()
  if (loading) return <Loader />
  if (isAuthenticated) {
    const dest = location.state?.from && !isAuthPath(location.state.from)
      ? location.state.from : '/'
    return <Navigate to={dest} replace />
  }
  return children
}

function isAuthPath(path) {
  return ['/login', '/signup', '/forgot-password', '/verify-reset-code',
          '/reset-password', '/verify-email'].some(p => (path || '').startsWith(p))
}
