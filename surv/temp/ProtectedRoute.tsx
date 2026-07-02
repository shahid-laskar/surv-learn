import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { isAuthenticated, fetchMe } from '../api/client'

/**
 * Guards all authenticated routes.
 *
 * On mount it calls /auth/me to verify the stored token is still valid
 * against Kong (catches expired tokens, secret-rotation, or tokens issued
 * before Kong JWT was enabled). A 401/403 from that probe clears localStorage
 * and bounces the user to /login automatically — no manual cache-busting needed.
 */
export default function ProtectedRoute() {
  const [checking, setChecking] = useState(true)
  const [valid,    setValid]    = useState(false)

  useEffect(() => {
    if (!isAuthenticated()) {
      setChecking(false)
      return
    }

    fetchMe()
      .then(() => setValid(true))
      .catch(() => {
        // Token rejected by Kong or FastAPI — clear stale state
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        localStorage.removeItem('role')
        setValid(false)
      })
      .finally(() => setChecking(false))
  }, [])

  if (checking) {
    // Minimal splash while we probe the backend — avoids a flash to /login
    return (
      <div className="flex h-screen items-center justify-center bg-surface">
        <span className="text-xs text-muted font-mono animate-pulse">Verifying session…</span>
      </div>
    )
  }

  if (!valid) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
