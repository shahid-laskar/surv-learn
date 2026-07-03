import { useQuery } from '@tanstack/react-query'
import { HeartPulse, Camera, Database, Activity, Server, AlertTriangle } from 'lucide-react'
import { fetchHealthSummary, fetchCameraHealth, fetchStorageStats } from '../api/client'
import { formatDistanceToNow } from 'date-fns'

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
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-100 flex items-center gap-2">
          <HeartPulse className="text-accent" /> System Health
        </h1>
        <p className="text-muted mt-1">Real-time status of cameras, workers, and storage.</p>
      </header>

      {/* Top Stats */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-panel border border-border p-4 rounded-lg flex items-center justify-between">
            <div>
              <p className="text-sm text-muted">Total Cameras</p>
              <p className="text-2xl font-mono text-slate-100">{summary.total_cameras}</p>
            </div>
            <div className="size-10 rounded-full bg-border flex items-center justify-center">
              <Camera size={20} className="text-muted" />
            </div>
          </div>
          <div className="bg-panel border border-border p-4 rounded-lg flex items-center justify-between">
            <div>
              <p className="text-sm text-muted">Online</p>
              <p className="text-2xl font-mono text-online">{summary.online_cameras}</p>
            </div>
            <div className="size-10 rounded-full bg-online/10 flex items-center justify-center">
              <Activity size={20} className="text-online" />
            </div>
          </div>
          <div className="bg-panel border border-border p-4 rounded-lg flex items-center justify-between">
            <div>
              <p className="text-sm text-muted">Offline</p>
              <p className="text-2xl font-mono text-alert">{summary.offline_cameras}</p>
            </div>
            <div className="size-10 rounded-full bg-alert/10 flex items-center justify-center">
              <AlertTriangle size={20} className="text-alert" />
            </div>
          </div>
          <div className="bg-panel border border-border p-4 rounded-lg flex items-center justify-between">
            <div>
              <p className="text-sm text-muted">Database</p>
              <p className="text-lg font-mono text-slate-200 capitalize">{summary.worker_health.postgres}</p>
            </div>
            <div className="size-10 rounded-full bg-border flex items-center justify-center">
              <Database size={20} className="text-muted" />
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Camera List */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-medium text-slate-200 flex items-center gap-2">
            <Camera size={18} /> Camera Status
          </h2>
          <div className="bg-panel border border-border rounded-lg overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-border/50 text-muted">
                <tr>
                  <th className="px-4 py-2 font-medium">Camera ID</th>
                  <th className="px-4 py-2 font-medium">Name</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Last Seen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {cameras.map(cam => (
                  <tr key={cam.camera_id} className="hover:bg-border/20">
                    <td className="px-4 py-3 font-mono">{cam.camera_id}</td>
                    <td className="px-4 py-3 text-slate-300">{cam.name || '-'}</td>
                    <td className="px-4 py-3">
                      {cam.is_online ? (
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-online/10 text-online text-xs font-medium">
                          <span className="size-1.5 rounded-full bg-online animate-pulse" /> Online
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-alert/10 text-alert text-xs font-medium">
                          <span className="size-1.5 rounded-full bg-alert" /> 
                          {cam.offline_minutes ? `Offline (${cam.offline_minutes}m)` : 'Offline'}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-muted">
                      {cam.last_seen ? formatDistanceToNow(new Date(cam.last_seen), { addSuffix: true }) : 'Never'}
                    </td>
                  </tr>
                ))}
                {cameras.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-muted">No cameras found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Storage Stats */}
        <div className="space-y-4">
          <h2 className="text-lg font-medium text-slate-200 flex items-center gap-2">
            <Server size={18} /> Storage
          </h2>
          
          {storage ? (
            <div className="space-y-3">
              {storage.buckets.map(b => (
                <div key={b.bucket} className="bg-panel border border-border p-4 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-mono text-sm text-slate-200">{b.bucket}</span>
                    <span className="text-xs text-muted bg-border px-2 py-1 rounded">MinIO</span>
                  </div>
                  <div className="space-y-1">
                    <p className="text-2xl font-mono text-slate-100">{b.total_size_gb.toFixed(2)} <span className="text-sm text-muted">GB</span></p>
                    <p className="text-xs text-muted">{b.object_count} objects</p>
                    {b.oldest_object && (
                      <p className="text-xs text-muted mt-2 pt-2 border-t border-border">
                        Oldest: {formatDistanceToNow(new Date(b.oldest_object), { addSuffix: true })}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-panel border border-border p-4 rounded-lg text-center text-muted text-sm py-8">
              Loading storage stats...
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
