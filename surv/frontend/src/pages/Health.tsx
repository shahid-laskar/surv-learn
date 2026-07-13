import { useQuery } from '@tanstack/react-query'
import { HeartPulse, Camera, Database, Activity, Server, AlertTriangle } from 'lucide-react'
import { fetchHealthSummary, fetchCameraHealth, fetchStorageStats } from '../api/client'
import { formatDistanceToNow } from 'date-fns'

function StatCard({ label, value, sub, icon: Icon, tone }: {
  label: string; value: string; sub?: string; icon: React.ElementType
  tone: 'default' | 'success' | 'danger'
}) {
  const iconBg = tone === 'success' ? 'oklch(0.72 0.17 150 / 0.1)'
               : tone === 'danger'  ? 'oklch(0.62 0.22 25 / 0.1)'
               : 'var(--color-secondary)'
  const iconColor = tone === 'success' ? 'var(--color-success)'
                  : tone === 'danger'  ? 'var(--color-destructive)'
                  : 'var(--color-muted-foreground)'
  return (
    <div className="rounded-xl p-4 flex items-center justify-between"
         style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
      <div>
        <p className="text-xs font-medium" style={{ color: 'var(--color-muted-foreground)' }}>{label}</p>
        <p className="text-2xl font-mono mt-1"
           style={{ fontFamily: 'var(--font-display)', color: tone === 'success' ? 'var(--color-success)' : tone === 'danger' ? 'var(--color-destructive)' : 'var(--color-foreground)' }}>
          {value}
        </p>
        {sub && <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>{sub}</p>}
      </div>
      <div className="size-10 rounded-full flex items-center justify-center"
           style={{ background: iconBg }}>
        <Icon size={18} style={{ color: iconColor }} />
      </div>
    </div>
  )
}

export default function Health() {
  const { data: summary } = useQuery({
    queryKey: ['health-summary'],
    queryFn: fetchHealthSummary,
    refetchInterval: 15_000,
  })

  const { data: cameras = [] } = useQuery({
    queryKey: ['health-cameras'],
    queryFn: fetchCameraHealth,
    refetchInterval: 15_000,
  })

  const { data: storage } = useQuery({
    queryKey: ['health-storage'],
    queryFn: fetchStorageStats,
    refetchInterval: 60_000,
  })

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div>
        <h1 className="text-base font-semibold flex items-center gap-2"
            style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
          <HeartPulse size={16} style={{ color: 'var(--color-primary)' }} />
          System Health
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
          Real-time status of cameras, workers, and storage.
        </p>
      </div>

      {/* KPI cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Total Cameras" value={String(summary.total_cameras)} icon={Camera} tone="default" />
          <StatCard label="Online" value={String(summary.online_cameras)} sub="streaming" icon={Activity} tone="success" />
          <StatCard label="Offline" value={String(summary.offline_cameras)} sub={summary.offline_cameras > 0 ? 'needs attention' : 'all clear'} icon={AlertTriangle} tone={summary.offline_cameras > 0 ? 'danger' : 'default'} />
          <StatCard label="Database" value={summary.worker_health.postgres} icon={Database} tone={summary.worker_health.postgres === 'ok' ? 'success' : 'danger'} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Camera list */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-semibold flex items-center gap-2"
              style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            <Camera size={15} style={{ color: 'var(--color-primary)' }} />
            Camera Status
          </h2>
          <div className="rounded-2xl overflow-hidden"
               style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="text-[11px] font-medium uppercase tracking-widest"
                    style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)' }}>
                  <th className="px-4 py-3">Camera ID</th>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {cameras.map(cam => (
                  <tr key={cam.camera_id} className="transition-colors last:border-b-0"
                      style={{ borderBottom: '1px solid var(--color-border)' }}
                      onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)')}
                      onMouseOut={e => (e.currentTarget.style.background = 'transparent')}>
                    <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--color-foreground)' }}>{cam.camera_id}</td>
                    <td className="px-4 py-3 text-xs" style={{ color: 'var(--color-muted-foreground)' }}>{cam.name || '—'}</td>
                    <td className="px-4 py-3">
                      {cam.is_online ? (
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium"
                              style={{ background: 'oklch(0.72 0.17 150 / 0.1)', color: 'var(--color-success)' }}>
                          <span className="size-1.5 rounded-full animate-pulse" style={{ background: 'var(--color-success)' }} />
                          Online
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium"
                              style={{ background: 'oklch(0.62 0.22 25 / 0.1)', color: 'var(--color-destructive)' }}>
                          <span className="size-1.5 rounded-full" style={{ background: 'var(--color-destructive)' }} />
                          {cam.offline_minutes ? `Offline (${cam.offline_minutes}m)` : 'Offline'}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
                      {cam.last_seen ? formatDistanceToNow(new Date(cam.last_seen), { addSuffix: true }) : 'Never'}
                    </td>
                  </tr>
                ))}
                {cameras.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-sm"
                        style={{ color: 'var(--color-muted-foreground)' }}>
                      No cameras found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Storage */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold flex items-center gap-2"
              style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            <Server size={15} style={{ color: 'var(--color-primary)' }} />
            Storage
          </h2>
          {storage ? (
            <div className="space-y-3">
              {storage.buckets.map(b => (
                <div key={b.bucket} className="rounded-xl p-4"
                     style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-mono text-sm" style={{ color: 'var(--color-foreground)' }}>{b.bucket}</span>
                    <span className="text-xs px-2 py-0.5 rounded-md"
                          style={{ background: 'var(--color-secondary)', color: 'var(--color-muted-foreground)' }}>
                      MinIO
                    </span>
                  </div>
                  <p className="text-2xl font-mono" style={{ color: 'var(--color-foreground)' }}>
                    {b.total_size_gb.toFixed(2)}{' '}
                    <span className="text-sm" style={{ color: 'var(--color-muted-foreground)' }}>GB</span>
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--color-muted-foreground)' }}>
                    {b.object_count} objects
                  </p>
                  {b.oldest_object && (
                    <p className="text-xs mt-2 pt-2" style={{ borderTop: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)' }}>
                      Oldest: {formatDistanceToNow(new Date(b.oldest_object), { addSuffix: true })}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl p-8 text-center text-sm"
                 style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)', color: 'var(--color-muted-foreground)' }}>
              Loading storage stats...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
