import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck, Loader2 } from 'lucide-react'
import { login } from '../api/client'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState<string | null>(null)
  const [loading, setLoading]   = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await login(username, password)
      localStorage.setItem('token', res.access_token)
      localStorage.setItem('username', res.username)
      localStorage.setItem('role', res.role)
      // Enriched RBAC fields (Phase 0003+)
      localStorage.setItem('user_type',    res.user_type ?? 'EMPLOYEE')
      localStorage.setItem('roles',        JSON.stringify(res.roles ?? []))
      localStorage.setItem('permissions',  JSON.stringify(res.permissions ?? []))
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4"
         style={{ background: 'var(--color-background)', color: 'var(--color-foreground)' }}>
      {/* Radial glow */}
      <div aria-hidden className="absolute inset-0 opacity-40 pointer-events-none"
           style={{ background: 'radial-gradient(60% 40% at 50% 0%, oklch(0.78 0.14 200 / 0.15) 0%, transparent 70%)' }} />

      <div className="relative w-full max-w-md">
        {/* Brand */}
        <div className="mb-8 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg"
               style={{ background: 'oklch(0.78 0.14 200 / 0.15)', boxShadow: '0 0 0 1px oklch(0.78 0.14 200 / 0.4)' }}>
            <ShieldCheck size={20} style={{ color: 'var(--color-primary)' }} />
          </div>
          <div>
            <div className="text-lg font-semibold tracking-tight"
                 style={{ fontFamily: 'var(--font-display)' }}>
              Sarvanetra
            </div>
            <div className="text-[11px] font-medium uppercase tracking-widest"
                 style={{ color: 'var(--color-muted-foreground)' }}>
              Operator console
            </div>
          </div>
        </div>

        {/* Card */}
        <form
          onSubmit={handleSubmit}
          className="rounded-2xl p-6"
          style={{
            border: '1px solid var(--color-border)',
            background: 'oklch(0.22 0.035 260 / 0.6)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
          }}
        >
          <h1 className="text-xl font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            Sign in
          </h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--color-muted-foreground)' }}>
            Sarvanetra Surveillance API · secure session
          </p>

          <div className="mt-6 space-y-4">
            <label className="block">
              <span className="text-xs font-medium uppercase tracking-widest"
                    style={{ color: 'var(--color-muted-foreground)' }}>
                Username
              </span>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
                autoFocus
                autoComplete="username"
                className="mt-1.5 block w-full rounded-lg px-3 py-2 text-sm outline-none transition-all"
                style={{
                  background: 'oklch(0.28 0.03 260 / 0.5)',
                  color: 'var(--color-foreground)',
                  boxShadow: '0 0 0 1px var(--color-border)',
                }}
                onFocus={e => (e.currentTarget.style.boxShadow = '0 0 0 1.5px oklch(0.78 0.14 200 / 0.6)')}
                onBlur={e => (e.currentTarget.style.boxShadow = '0 0 0 1px var(--color-border)')}
                placeholder="operator"
              />
            </label>
            <label className="block">
              <span className="text-xs font-medium uppercase tracking-widest"
                    style={{ color: 'var(--color-muted-foreground)' }}>
                Password
              </span>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="mt-1.5 block w-full rounded-lg px-3 py-2 text-sm outline-none transition-all"
                style={{
                  background: 'oklch(0.28 0.03 260 / 0.5)',
                  color: 'var(--color-foreground)',
                  boxShadow: '0 0 0 1px var(--color-border)',
                }}
                onFocus={e => (e.currentTarget.style.boxShadow = '0 0 0 1.5px oklch(0.78 0.14 200 / 0.6)')}
                onBlur={e => (e.currentTarget.style.boxShadow = '0 0 0 1px var(--color-border)')}
                placeholder="••••••••"
              />
            </label>
          </div>

          {error && (
            <div className="mt-4 rounded-lg px-3 py-2 text-xs"
                 style={{ border: '1px solid oklch(0.62 0.22 25 / 0.3)', background: 'oklch(0.62 0.22 25 / 0.1)', color: 'var(--color-destructive)' }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-6 inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg text-sm font-semibold transition-all disabled:opacity-60"
            style={{
              background: 'var(--color-primary)',
              color: 'var(--color-primary-foreground)',
            }}
            onMouseOver={e => { if (!loading) e.currentTarget.style.filter = 'brightness(1.1)' }}
            onMouseOut={e => { e.currentTarget.style.filter = 'none' }}
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : null}
            Sign in
          </button>
        </form>

        <p className="mt-6 text-center text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
          Trouble signing in? Contact your organization administrator.
        </p>
      </div>
    </div>
  )
}
