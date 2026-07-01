import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, Lock, User as UserIcon } from 'lucide-react'
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
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center h-screen bg-surface">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm bg-panel border border-border rounded-lg p-6
                   flex flex-col gap-4 animate-[fade-in_0.2s_ease-out]"
      >
        <div className="flex flex-col items-center gap-2 mb-2">
          <div className="size-10 rounded bg-accent/20 flex items-center justify-center">
            <Activity size={18} className="text-accent" />
          </div>
          <p className="text-sm font-semibold text-slate-100">Sarvanetra</p>
          <p className="font-mono text-[10px] text-muted tracking-widest">SURVEILLANCE</p>
        </div>

        <div>
          <label className="block text-xs text-muted mb-1">Username</label>
          <div className="relative">
            <UserIcon size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoFocus
              className="w-full bg-surface border border-border rounded pl-9 pr-3 py-2
                         text-sm text-slate-200 placeholder-muted focus:outline-none
                         focus:border-accent/60 transition-colors"
              placeholder="operator"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs text-muted mb-1">Password</label>
          <div className="relative">
            <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="w-full bg-surface border border-border rounded pl-9 pr-3 py-2
                         text-sm text-slate-200 placeholder-muted focus:outline-none
                         focus:border-accent/60 transition-colors"
              placeholder="••••••••"
            />
          </div>
        </div>

        {error && <p className="text-xs text-alert">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="mt-2 px-3 py-2 bg-accent hover:bg-accent/80 text-white text-sm
                     font-medium rounded transition-colors disabled:opacity-50"
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}
