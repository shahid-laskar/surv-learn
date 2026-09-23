import { Routes, Route, Navigate } from 'react-router-dom'
import { Bell, Activity, Languages } from 'lucide-react'
import Sidebar         from './components/Sidebar'
import ProtectedRoute  from './components/ProtectedRoute'
import Login            from './pages/Login'
import LiveView         from './pages/LiveView'
import IcccCommand      from './pages/IcccCommand'
import ParkingManagement from './pages/ParkingManagement'
import AnprManagement   from './pages/AnprManagement'
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
import { useI18n }       from './lib/i18n'

function AppShell() {
  const { t, toggleLanguage } = useI18n()
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
              {t('system_nominal')}
            </span>
          </div>

          <div className="flex items-center gap-3 ml-auto">
            {/* Language switcher */}
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 transition"
              title="Toggle Malayalam / English"
            >
              <Languages size={13} className="text-sky-400" />
              <span>{t('switch_language')}</span>
            </button>

            {/* Activity */}
            <div className="hidden items-center gap-1.5 text-[11px] md:flex"
                 style={{ color: 'var(--color-muted-foreground)' }}>
              <Activity size={12} />
              {t('realtime_connected')}
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
            <Route path="/iccc"          element={<IcccCommand />}  />
            <Route path="/parking"       element={<ParkingManagement />} />
            <Route path="/anpr"          element={<AnprManagement />} />
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
            <Route path="/fleet"         element={<NvrFleet />}     />
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
