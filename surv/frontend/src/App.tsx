import { Routes, Route, Navigate } from 'react-router-dom'
import { Bell, Activity } from 'lucide-react'
import Sidebar         from './components/Sidebar'
import ProtectedRoute  from './components/ProtectedRoute'
import Login            from './pages/Login'
import LiveView         from './pages/LiveView'
import Playback         from './pages/Playback'
import MotionEvents     from './pages/MotionEvents'
import Cameras          from './pages/Cameras'
import Organizations    from './pages/Organizations'
import Customers        from './pages/Customers'
import Users            from './pages/Users'
import Roles            from './pages/Roles'
import AuditLog         from './pages/AuditLog'
import CameraGroups     from './pages/CameraGroups'
import Health           from './pages/Health'
import NvrFleet         from './pages/NvrFleet'

function AppShell() {
  const username = localStorage.getItem('username') ?? 'user'
  const initials = username
    .split(/\s+/)
    .map(s => s[0]?.toUpperCase() ?? '')
    .join('')
    .slice(0, 2) || '?'

  return (
    <div className="flex h-screen overflow-hidden"
         style={{ background: 'var(--color-background)', color: 'var(--color-foreground)' }}>
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Sticky header */}
        <header className="flex h-14 shrink-0 items-center justify-between px-4 lg:px-6"
                style={{
                  borderBottom: '1px solid var(--color-border)',
                  background: 'oklch(0.19 0.04 260 / 0.7)',
                  backdropFilter: 'blur(12px)',
                  WebkitBackdropFilter: 'blur(12px)',
                }}>
          {/* System status */}
          <div className="hidden items-center gap-2 md:flex">
            <span className="size-2 rounded-full animate-[pulse-dot_2s_ease-in-out_infinite]"
                  style={{ background: 'var(--color-success)' }} />
            <span className="text-xs font-medium" style={{ color: 'var(--color-muted-foreground)' }}>
              System nominal
            </span>
          </div>

          <div className="flex items-center gap-3 ml-auto">
            {/* Activity */}
            <div className="hidden items-center gap-1.5 text-[11px] md:flex"
                 style={{ color: 'var(--color-muted-foreground)' }}>
              <Activity size={12} />
              Realtime · connected
            </div>

            {/* Bell */}
            <button className="relative rounded-lg p-2 transition-colors"
                    style={{ color: 'var(--color-muted-foreground)' }}
                    onMouseOver={e => (e.currentTarget.style.background = 'var(--color-secondary)')}
                    onMouseOut={e => (e.currentTarget.style.background = 'transparent')}>
              <Bell size={16} />
              <span className="absolute right-1.5 top-1.5 size-1.5 rounded-full"
                    style={{ background: 'var(--color-destructive)' }} />
            </button>

            {/* Avatar */}
            <div className="flex size-8 items-center justify-center rounded-full text-xs font-semibold"
                 style={{
                   background: 'var(--color-secondary)',
                   color: 'var(--color-foreground)',
                   boxShadow: '0 0 0 1px var(--color-border)',
                 }}
                 title={username}>
              {initials}
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto min-w-0">
          <Routes>
            <Route path="/"              element={<LiveView />}     />
            <Route path="/playback"      element={<Playback />}     />
            <Route path="/motion"        element={<MotionEvents />} />
            <Route path="/cameras"       element={<Cameras />}      />
            <Route path="/health"        element={<Health />}       />
            <Route path="/org"           element={<Organizations />} />
            <Route path="/customers"     element={<Customers />}    />
            <Route path="/users"         element={<Users />}        />
            <Route path="/roles"         element={<Roles />}        />
            <Route path="/audit"         element={<AuditLog />}     />
            <Route path="/camera-groups" element={<CameraGroups />} />
            <Route path="/fleet"         element={<NvrFleet />} />
            <Route path="*"              element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/*" element={<AppShell />} />
      </Route>
    </Routes>
  )
}
