import { NavLink } from 'react-router-dom'
import {
  Video, PlaySquare, Bell, Camera, Activity, LogOut, HeartPulse,
  Building2, Users, ShieldCheck, ClipboardList, Layers, UserCog,
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

  const onlineCount  = cameras.filter(c => c.is_online).length
  const offlineCount = cameras.length - onlineCount
  const username  = localStorage.getItem('username') ?? 'user'
  const userType  = getUserType()
  const roles     = getRoles()
  const isAdmin   = hasRole('SUPER_ADMIN')

  const NAV: NavItem[] = [
    // ── Always visible ────────────────────────────────────
    { to: '/',         icon: Video,          label: 'Live View',      show: true },
    { to: '/playback', icon: PlaySquare,     label: 'Playback',       show: true },
    { to: '/motion',   icon: Bell,           label: 'Motion Alerts',  badge: activeMotion.length, show: true },
    { to: '/cameras',  icon: Camera,         label: 'Cameras',        show: true },
    { to: '/health',   icon: HeartPulse,     label: 'Health',         badge: offlineCount > 0 ? offlineCount : undefined, show: hasPermission('system.settings') || isAdmin },
    // ── Camera Groups — visible to anyone with camera.view ─
    { to: '/camera-groups', icon: Layers,    label: 'Camera Groups',  show: hasPermission('camera.view') || isAdmin },
    // ── Admin / manager pages ─────────────────────────────
    { to: '/org',      icon: Building2,      label: 'Organizations',  show: hasPermission('system.settings') || isAdmin },
    { to: '/customers',icon: UserCog,        label: 'Customers',      show: true },
    { to: '/users',    icon: Users,          label: 'Users',          show: hasPermission('user.view') || isAdmin },
    { to: '/roles',    icon: ShieldCheck,    label: 'Roles & Perms',  show: hasPermission('system.settings') || isAdmin },
    { to: '/audit',    icon: ClipboardList,  label: 'Audit Log',      show: hasPermission('system.audit') || isAdmin },
  ]

  return (
    <aside className="flex flex-col w-56 h-screen bg-panel border-r border-border shrink-0">

      {/* Logo */}
      <div className="px-4 py-5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="size-7 rounded bg-accent/20 flex items-center justify-center">
            <Activity size={14} className="text-accent" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-100 leading-none">Sarvanetra</p>
            <p className="font-mono text-[10px] text-muted mt-0.5 tracking-widest">SURVEILLANCE</p>
          </div>
        </div>
      </div>

      {/* Status strip */}
      <div className="px-4 py-2.5 border-b border-border flex items-center gap-4 text-xs">
        <span className="flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-online animate-[pulse-dot_2s_ease-in-out_infinite]" />
          <span className="text-online font-mono">{onlineCount}</span>
          <span className="text-muted">online</span>
        </span>
        {offlineCount > 0 && (
          <span className="flex items-center gap-1.5">
            <span className="size-1.5 rounded-full bg-alert" />
            <span className="text-alert font-mono">{offlineCount}</span>
            <span className="text-muted">down</span>
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {NAV.filter(n => n.show !== false).map(({ to, icon: Icon, label, badge }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded text-sm font-medium
               transition-colors duration-150 cursor-pointer select-none
               ${isActive
                 ? 'bg-accent/10 text-accent'
                 : 'text-muted hover:bg-border hover:text-slate-200'
               }`
            }
          >
            <Icon size={15} />
            <span>{label}</span>
            {badge != null && badge > 0 && (
              <span className="ml-auto bg-alert text-white font-mono text-[10px]
                               px-1.5 py-0.5 rounded-full leading-none">
                {badge}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Camera quick-list */}
      <div className="border-t border-border px-2 py-3">
        <p className="px-3 font-mono text-[10px] text-muted uppercase tracking-widest mb-2">
          Cameras
        </p>
        <div className="space-y-0.5 max-h-32 overflow-y-auto">
          {cameras.map(cam => (
            <NavLink
              key={cam.cam_id}
              to={`/playback?cam=${cam.cam_id}`}
              className="flex items-center gap-2 px-3 py-1.5 rounded
                         hover:bg-border/50 transition-colors duration-100 group"
            >
              <span className={`size-1.5 rounded-full shrink-0 ${
                cam.is_online
                  ? 'bg-online animate-[pulse-dot_2s_ease-in-out_infinite]'
                  : 'bg-dim'
              }`} />
              <span className="font-mono text-xs text-muted group-hover:text-slate-300
                               truncate transition-colors">
                {cam.cam_id}
              </span>
            </NavLink>
          ))}
          {cameras.length === 0 && (
            <p className="px-3 text-xs text-muted/60 italic">No cameras</p>
          )}
        </div>
      </div>

      {/* User / logout */}
      <div className="border-t border-border px-4 py-3 flex items-center justify-between">
        <div className="min-w-0">
          <p className="text-xs text-slate-300 truncate">{username}</p>
          <div className="flex items-center gap-1 mt-0.5 flex-wrap">
            <span className="font-mono text-[9px] text-muted uppercase">{userType}</span>
            {roles.slice(0, 2).map(r => (
              <span key={r} className="font-mono text-[8px] bg-accent/10 text-accent px-1 rounded leading-tight">
                {r.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
        <button
          onClick={() => callLogout()}
          title="Log out"
          className="p-1.5 text-muted hover:text-alert hover:bg-border rounded transition-colors"
        >
          <LogOut size={14} />
        </button>
      </div>
    </aside>
  )
}
