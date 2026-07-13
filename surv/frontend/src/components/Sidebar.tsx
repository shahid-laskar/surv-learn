import { NavLink } from 'react-router-dom'
import {
  Video, PlaySquare, Bell, Camera, HeartPulse,
  Building2, Users, LogOut, ShieldCheck, ClipboardList,
  Layers, UserCog, Server, Activity,
} from 'lucide-react'
import { usePolling } from '../hooks/usePolling'
import {
  fetchCameras,
  fetchActiveMotion,
  callLogout,
  type Camera as CameraType,
  type MotionEvent,
} from '../api/client'
import { hasPermission, hasRole, getRoles, getUserType } from '../lib/auth'

// UI failsafe: if the backend misses a `motion_end`, avoid showing the same
// alert as "active forever".
const STALE_ACTIVE_MS = 30 * 60 * 1000 // 30 minutes

function effectiveIsActive(e: MotionEvent): boolean {
  if (!e.is_active) return false
  if (e.motion_end) return e.is_active
  const startMs = new Date(e.motion_start).getTime()
  const ageMs = Date.now() - startMs
  return ageMs < STALE_ACTIVE_MS
}

type NavItem = {
  to: string
  icon: React.ElementType
  label: string
  badge?: number
  show?: boolean
}

export default function Sidebar() {
  const { data: cameras      = [] } = usePolling<CameraType[]>(['cameras'],      fetchCameras,      20_000)
  const { data: activeMotion = [] } = usePolling<MotionEvent[]>(['motion-active'], fetchActiveMotion, 10_000)
  const activeMotionCount = activeMotion.filter(e => effectiveIsActive(e)).length

  const onlineCount  = cameras.filter(c => c.is_online).length
  const offlineCount = cameras.length - onlineCount
  const username  = localStorage.getItem('username') ?? 'user'
  const userType  = getUserType()
  const roles     = getRoles()
  const isAdmin   = hasRole('SUPER_ADMIN')
  const systemOk  = offlineCount === 0

  // Generate avatar initials
  const initials = username
    .split(/\s+/)
    .map(s => s[0]?.toUpperCase() ?? '')
    .join('')
    .slice(0, 2) || '?'

  const NAV: NavItem[] = [
    // ── Always visible ────────────────────────────────────
    { to: '/',         icon: Video,          label: 'Live View',      show: true },
    { to: '/playback', icon: PlaySquare,     label: 'Playback',       show: true },
    { to: '/motion',   icon: Bell,           label: 'Motion Alerts',  badge: activeMotionCount, show: true },
    { to: '/cameras',  icon: Camera,         label: 'Cameras',        show: true },
    { to: '/health',   icon: HeartPulse,     label: 'Health',         badge: offlineCount > 0 ? offlineCount : undefined, show: hasPermission('system.settings') || isAdmin },
    // ── Camera Groups — visible to anyone with camera.view ─
    { to: '/camera-groups', icon: Layers,    label: 'Camera Groups',  show: hasPermission('camera.view') || isAdmin },
    // ── Admin / manager pages ─────────────────────────────
    { to: '/fleet',    icon: Server,         label: 'NVR Fleet',      show: hasRole('SUPER_ADMIN') || hasRole('INSTALLER') },
    { to: '/org',      icon: Building2,      label: 'Organizations',  show: hasPermission('system.settings') || isAdmin },
    { to: '/customers',icon: UserCog,        label: 'Customers',      show: true },
    { to: '/users',    icon: Users,          label: 'Users',          show: hasPermission('user.view') || isAdmin },
    { to: '/roles',    icon: ShieldCheck,    label: 'Roles & Perms',  show: hasPermission('system.settings') || isAdmin },
    { to: '/audit',    icon: ClipboardList,  label: 'Audit Log',      show: hasPermission('system.audit') || isAdmin },
  ]

  return (
    <aside className="hidden lg:flex flex-col w-64 h-screen shrink-0 border-r"
           style={{ background: 'var(--color-sidebar)', borderColor: 'var(--color-border)' }}>

      {/* Logo */}
      <div className="px-4 py-5 mb-2">
        <div className="flex items-center gap-3 px-2">
          <div className="flex size-9 items-center justify-center rounded-lg"
               style={{ background: 'oklch(0.78 0.14 200 / 0.15)', boxShadow: '0 0 0 1px oklch(0.78 0.14 200 / 0.4)' }}>
            <ShieldCheck size={16} style={{ color: 'var(--color-primary)' }} />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold tracking-tight"
                  style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
              Sarvanetra
            </span>
            <span className="text-[10px] font-medium uppercase tracking-widest"
                  style={{ color: 'var(--color-muted-foreground)' }}>
              Surveillance
            </span>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto">
        {NAV.filter(n => n.show !== false).map(({ to, icon: Icon, label, badge }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium
               transition-colors duration-150 cursor-pointer select-none
               ${isActive
                 ? 'text-foreground'
                 : 'text-muted-foreground hover:text-foreground'
               }`
            }
            style={({ isActive }) => isActive
              ? { background: 'var(--color-secondary)', color: 'var(--color-foreground)' }
              : undefined
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={15} style={{ color: isActive ? 'var(--color-primary)' : 'var(--color-muted-foreground)', flexShrink: 0 }} />
                <span>{label}</span>
                {badge != null && badge > 0 && (
                  <span className="ml-auto font-mono text-[10px] px-1.5 py-0.5 rounded-full leading-none text-white"
                        style={{ background: 'var(--color-destructive)' }}>
                    {badge}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Camera quick-list */}
      <div className="px-3 py-3" style={{ borderTop: '1px solid var(--color-border)' }}>
        <p className="px-3 font-mono text-[10px] uppercase tracking-widest mb-2"
           style={{ color: 'var(--color-muted-foreground)' }}>
          Cameras
        </p>
        <div className="space-y-0.5 max-h-28 overflow-y-auto">
          {cameras.map(cam => (
            <NavLink
              key={cam.cam_id}
              to={`/playback?cam=${cam.cam_id}`}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg
                         transition-colors duration-100 group"
              style={{ color: 'var(--color-muted-foreground)' }}
            >
              <span className={`size-1.5 rounded-full shrink-0 ${
                cam.is_online
                  ? 'animate-[pulse-dot_2s_ease-in-out_infinite]'
                  : ''
              }`}
                    style={{ background: cam.is_online ? 'var(--color-success)' : 'var(--color-dim)' }} />
              <span className="font-mono text-xs truncate transition-colors"
                    style={{ color: 'var(--color-muted-foreground)' }}>
                {cam.cam_id}
              </span>
            </NavLink>
          ))}
          {cameras.length === 0 && (
            <p className="px-3 text-xs italic" style={{ color: 'oklch(0.68 0.02 260 / 0.6)' }}>No cameras</p>
          )}
        </div>
      </div>

      {/* Status + User footer */}
      <div className="px-4 py-3 space-y-3" style={{ borderTop: '1px solid var(--color-border)' }}>
        {/* System health */}
        <div className="rounded-xl p-3"
             style={{ border: '1px solid var(--color-border)', background: 'oklch(0.22 0.035 260 / 0.6)' }}>
          <div className="flex items-center gap-2 mb-1">
            <span className="relative flex size-2">
              <span className={`absolute inline-flex h-full w-full rounded-full opacity-60 ${
                systemOk ? 'animate-ping' : ''
              }`}
                    style={{ background: systemOk ? 'oklch(0.78 0.14 200 / 0.7)' : 'oklch(0.62 0.22 25 / 0.7)' }} />
              <span className="relative inline-flex size-2 rounded-full"
                    style={{ background: systemOk ? 'var(--color-primary)' : 'var(--color-destructive)' }} />
            </span>
            <span className="text-xs font-semibold" style={{ color: 'var(--color-foreground)' }}>
              {systemOk ? 'Services healthy' : 'Services degraded'}
            </span>
          </div>
          <p className="text-[11px] leading-relaxed" style={{ color: 'var(--color-muted-foreground)' }}>
            {onlineCount}/{cameras.length} cameras online
          </p>
        </div>

        {/* User row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="flex size-8 items-center justify-center rounded-full text-xs font-semibold shrink-0"
                 style={{ background: 'var(--color-secondary)', color: 'var(--color-foreground)', boxShadow: '0 0 0 1px var(--color-border)' }}>
              {initials}
            </div>
            <div className="min-w-0">
              <p className="text-xs truncate" style={{ color: 'var(--color-foreground)' }}>{username}</p>
              <div className="flex items-center gap-1 mt-0.5 flex-wrap">
                <span className="font-mono text-[9px] uppercase" style={{ color: 'var(--color-muted-foreground)' }}>{userType}</span>
                {roles.slice(0, 1).map(r => (
                  <span key={r} className="font-mono text-[8px] px-1 rounded leading-tight"
                        style={{ background: 'oklch(0.78 0.14 200 / 0.1)', color: 'var(--color-primary)' }}>
                    {r.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          </div>
          <button
            onClick={() => callLogout()}
            title="Log out"
            className="p-1.5 rounded-lg transition-colors"
            style={{ color: 'var(--color-muted-foreground)' }}
            onMouseOver={e => (e.currentTarget.style.color = 'var(--color-destructive)')}
            onMouseOut={e => (e.currentTarget.style.color = 'var(--color-muted-foreground)')}
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-3 text-[11px]" style={{ borderTop: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)' }}>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Activity size={11} />
            Realtime channel · connected
          </span>
        </div>
      </div>
    </aside>
  )
}
