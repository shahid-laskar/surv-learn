import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { Bell, BellOff, ExternalLink, Filter } from 'lucide-react'
import { fetchMotionEvents, fetchCameras, type MotionEvent } from '../api/client'

// Failsafe: if backend never receives a corresponding `motion_end`,
// treat very old "active" events as ended so the UI doesn't get stuck.
const STALE_ACTIVE_MS = 30 * 60 * 1000 // 30 minutes

function effectiveMotionEnd(e: MotionEvent): string | null {
  if (e.motion_end) return e.motion_end
  if (!e.is_active) return null

  const startMs = new Date(e.motion_start).getTime()
  const ageMs = Date.now() - startMs
  if (ageMs < STALE_ACTIVE_MS) return null

  // Approximate end time so the UI can display an Ended duration.
  return new Date(startMs + STALE_ACTIVE_MS).toISOString()
}

function effectiveIsActive(e: MotionEvent): boolean {
  // If we computed an effective end time, it's effectively ended in the UI.
  return effectiveMotionEnd(e) ? false : e.is_active
}

function dur(e: MotionEvent) {
  const end = effectiveMotionEnd(e)
  if (!end) return '—'
  const s = Math.round((new Date(end).getTime() - new Date(e.motion_start).getTime()) / 1000)
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`
}

export default function MotionEvents() {
  const navigate = useNavigate()
  const [filterCam,    setFilterCam]    = useState('all')
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'ended'>('all')
  const [limit, setLimit] = useState(100)

  const { data: cameras = [], error: camerasError, isFetching: isFetchingCameras, refetch: refetchCameras } = useQuery({
    queryKey: ['cameras'],
    queryFn:  fetchCameras,
    // Keep camera metadata reasonably fresh and self-healing after transient failures.
    refetchInterval:      20_000,
    refetchOnReconnect:   true,
    refetchOnWindowFocus: true,
    retry:                3,
  })
  const camMap = Object.fromEntries(cameras.map(c => [c.id, c]))

  const { data: events = [], isFetching, error: eventsError, refetch } = useQuery({
    // We fetch unfiltered motion events and apply the active/ended filter client-side.
    // This keeps the UI consistent even if the backend momentarily misses a `motion_end`.
    queryKey:       ['motion', filterCam, limit],
    queryFn:        () => fetchMotionEvents({
      camera_id: filterCam !== 'all' ? cameras.find(c => c.cam_id === filterCam)?.id : undefined,
      active:    undefined,
      limit,
    }),
    // Periodic polling so we don't rely solely on manual refresh.
    refetchInterval:      10_000,
    refetchOnReconnect:   true,
    refetchOnWindowFocus: true,
    // Allow a few quick retries on transient network errors; subsequent
    // interval polls + manual "Refresh" will also continue to heal.
    retry:                3,
  })

  const activeCount = events.filter(e => effectiveIsActive(e)).length
  const filteredEvents =
    filterActive === 'all'
      ? events
      : filterActive === 'active'
        ? events.filter(e => effectiveIsActive(e))
        : events.filter(e => !effectiveIsActive(e))

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
        <div className="flex items-center gap-2">
          {(camerasError || eventsError) && (
            <span className="text-[10px] font-mono text-alert bg-alert/10 border border-alert/40 rounded px-2 py-1">
              Network issue — will retry
            </span>
          )}
          <button
            onClick={() => {
              refetchCameras()
              refetch()
            }}
            className="px-3 py-1.5 text-muted hover:text-slate-200 text-xs font-medium
                       rounded hover:bg-border transition-colors"
          >
            {isFetching || isFetchingCameras ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
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
          {isFetching ? 'Refreshing...' : `${filteredEvents.length} events`}
        </span>
      </div>

      {/* Table */}
      <div className="flex-1 bg-panel border border-border rounded overflow-hidden flex flex-col min-h-0">
        <div className="overflow-y-auto flex-1">
          {filteredEvents.length === 0 ? (
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
                {filteredEvents.map(ev => {
                  const cam = camMap[ev.camera_id]
                  return (
                    <tr key={ev.id}
                        className="border-b border-border/50 hover:bg-border/30 transition-colors">
                      <td className="px-4 py-2.5">
                        <span className="flex items-center gap-1.5">
                          <span className={`size-1.5 rounded-full ${effectiveIsActive(ev) ? 'bg-alert animate-[pulse-dot_2s_ease-in-out_infinite]' : 'bg-dim'}`} />
                          <span className={`font-mono text-[10px] ${effectiveIsActive(ev) ? 'text-alert' : 'text-muted'}`}>
                            {effectiveIsActive(ev) ? 'ACTIVE' : 'ENDED'}
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
                        {effectiveMotionEnd(ev) ? (
                          format(new Date(effectiveMotionEnd(ev) as string), 'HH:mm:ss')
                        ) : (
                          <span className="text-alert">—</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-muted">{dur(ev)}</td>
                      <td className="px-4 py-2.5 text-right">
                        <button
                          onClick={() => {
                            const startIso = new Date(ev.motion_start).toISOString()
                            const d        = format(new Date(ev.motion_start), 'yyyy-MM-dd')
                            navigate(`/playback?cam=${cam?.cam_id}&date=${d}&start=${encodeURIComponent(startIso)}`)
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
