import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { Bell, BellOff, ExternalLink, Filter } from 'lucide-react'
import { fetchMotionEvents, fetchCameras, type MotionEvent } from '../api/client'

function dur(e: MotionEvent) {
  if (!e.motion_end) return '—'
  const s = Math.round((new Date(e.motion_end).getTime() - new Date(e.motion_start).getTime()) / 1000)
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`
}

export default function MotionEvents() {
  const navigate = useNavigate()
  const [filterCam,    setFilterCam]    = useState('all')
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'ended'>('all')
  const [limit, setLimit] = useState(100)

  const { data: cameras = [] } = useQuery({ queryKey: ['cameras'], queryFn: fetchCameras })
  const camMap = Object.fromEntries(cameras.map(c => [c.id, c]))

  const { data: events = [], isFetching, refetch } = useQuery({
    queryKey:       ['motion', filterCam, filterActive, limit],
    queryFn:        () => fetchMotionEvents({
      camera_id: filterCam !== 'all' ? cameras.find(c => c.cam_id === filterCam)?.id : undefined,
      active:    filterActive === 'all' ? undefined : filterActive === 'active',
      limit,
    }),
    refetchInterval: 10_000,
  })

  const activeCount = events.filter(e => e.is_active).length

  return (
    <div className="flex flex-col h-full p-4 gap-4 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-base font-semibold text-slate-100">Motion Alerts</h1>
            <p className="text-xs text-muted mt-0.5">
              {activeCount > 0 ? `${activeCount} active right now` : 'No active motion'}
            </p>
          </div>
          {activeCount > 0 && (
            <span className="flex items-center gap-1.5 bg-alert/10 border border-alert/30
                             text-alert font-mono text-xs px-2 py-1 rounded
                             animate-[pulse-dot_2s_ease-in-out_infinite]">
              <Bell size={11} /> {activeCount} ACTIVE
            </span>
          )}
        </div>
        <button onClick={() => refetch()}
                className="px-3 py-1.5 text-muted hover:text-slate-200 text-xs font-medium
                           rounded hover:bg-border transition-colors">
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 shrink-0">
        <Filter size={13} className="text-muted" />
        <select
          value={filterCam}
          onChange={e => setFilterCam(e.target.value)}
          className="bg-surface border border-border rounded px-3 py-1.5 text-sm
                     text-slate-200 focus:outline-none focus:border-accent/60 w-44"
        >
          <option value="all">All cameras</option>
          {cameras.map(c => <option key={c.cam_id} value={c.cam_id}>{c.cam_name ?? c.cam_id}</option>)}
        </select>

        <div className="flex items-center gap-1 bg-panel border border-border rounded p-1">
          {(['all', 'active', 'ended'] as const).map(f => (
            <button key={f} onClick={() => setFilterActive(f)}
                    className={`px-2.5 py-1 rounded text-xs font-medium capitalize transition-colors
                                ${filterActive === f
                                  ? f === 'active' ? 'bg-alert/20 text-alert' : 'bg-accent/20 text-accent'
                                  : 'text-muted hover:text-slate-200'}`}>
              {f}
            </button>
          ))}
        </div>

        <span className="text-xs text-muted ml-auto">
          {isFetching ? 'Refreshing...' : `${events.length} events`}
        </span>
      </div>

      {/* Table */}
      <div className="flex-1 bg-panel border border-border rounded overflow-hidden flex flex-col min-h-0">
        <div className="overflow-y-auto flex-1">
          {events.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-3">
              <BellOff size={28} className="text-dim" />
              <p className="text-sm text-muted">No motion events found</p>
            </div>
          ) : (
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-panel border-b border-border z-10">
                <tr className="text-muted font-mono">
                  {['Status', 'Camera', 'Started', 'Ended', 'Duration', ''].map(h => (
                    <th key={h} className={`px-4 py-2.5 ${h === '' ? 'text-right' : 'text-left'}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {events.map(ev => {
                  const cam = camMap[ev.camera_id]
                  return (
                    <tr key={ev.id}
                        className="border-b border-border/50 hover:bg-border/30 transition-colors">
                      <td className="px-4 py-2.5">
                        <span className="flex items-center gap-1.5">
                          <span className={`size-1.5 rounded-full ${ev.is_active ? 'bg-alert animate-[pulse-dot_2s_ease-in-out_infinite]' : 'bg-dim'}`} />
                          <span className={`font-mono text-[10px] ${ev.is_active ? 'text-alert' : 'text-muted'}`}>
                            {ev.is_active ? 'ACTIVE' : 'ENDED'}
                          </span>
                        </span>
                      </td>
                      <td className="px-4 py-2.5">
                        <span className="font-mono text-slate-300">{cam?.cam_id ?? `id:${ev.camera_id}`}</span>
                        {cam?.cam_name && <span className="block text-muted text-[10px]">{cam.cam_name}</span>}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-slate-400">
                        {format(new Date(ev.motion_start), 'dd MMM HH:mm:ss')}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-muted">
                        {ev.motion_end ? format(new Date(ev.motion_end), 'HH:mm:ss') : <span className="text-alert">—</span>}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-muted">{dur(ev)}</td>
                      <td className="px-4 py-2.5 text-right">
                        <button
                          onClick={() => {
                            const d = format(new Date(ev.motion_start), 'yyyy-MM-dd')
                            navigate(`/playback?cam=${cam?.cam_id}&date=${d}`)
                          }}
                          title="Review recording"
                          className="text-accent hover:text-accent/70 transition-colors"
                        >
                          <ExternalLink size={11} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
        {events.length >= limit && (
          <div className="border-t border-border px-4 py-2 flex justify-center">
            <button onClick={() => setLimit(l => l + 100)}
                    className="px-3 py-1.5 text-muted hover:text-slate-200 text-xs font-medium rounded hover:bg-border transition-colors">
              Load more
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
