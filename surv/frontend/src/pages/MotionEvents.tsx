import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { Bell, BellOff, ExternalLink, Filter, AlertTriangle, ScanFace } from 'lucide-react'
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
  return new Date(startMs + STALE_ACTIVE_MS).toISOString()
}

function effectiveIsActive(e: MotionEvent): boolean {
  return effectiveMotionEnd(e) ? false : e.is_active
}

function dur(e: MotionEvent) {
  const end = effectiveMotionEnd(e)
  if (!end) return '—'
  const s = Math.round((new Date(end).getTime() - new Date(e.motion_start).getTime()) / 1000)
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`
}

// ── Reusable filter group ─────────────────────────────────
function FilterGroup<T extends string>({ label, value, onChange, options }: {
  label: string; value: T; onChange: (v: T) => void; options: readonly T[]
}) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[11px] font-medium uppercase tracking-widest"
            style={{ color: 'var(--color-muted-foreground)' }}>
        {label}
      </span>
      <div className="flex rounded-lg p-0.5"
           style={{ background: 'oklch(0.28 0.03 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
        {options.map(o => (
          <button
            key={o}
            onClick={() => onChange(o)}
            className="rounded-md px-2.5 py-1 text-xs font-medium capitalize transition-colors"
            style={{
              background: value === o ? 'var(--color-background)' : 'transparent',
              color: value === o ? 'var(--color-foreground)' : 'var(--color-muted-foreground)',
              boxShadow: value === o ? '0 1px 3px rgba(0,0,0,0.3)' : undefined,
            }}
          >
            {o}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Status pill ───────────────────────────────────────────
function StatePill({ active }: { active: boolean }) {
  return (
    <span className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider"
          style={{
            background: active ? 'oklch(0.78 0.15 75 / 0.1)' : 'oklch(0.72 0.17 150 / 0.1)',
            color: active ? 'var(--color-warning)' : 'var(--color-success)',
            boxShadow: `0 0 0 1px ${active ? 'oklch(0.78 0.15 75 / 0.25)' : 'oklch(0.72 0.17 150 / 0.25)'}`,
          }}>
      {active ? 'active' : 'resolved'}
    </span>
  )
}

export default function MotionEvents() {
  const navigate = useNavigate()
  const [filterCam,    setFilterCam]    = useState('all')
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'ended'>('all')
  const [limit, setLimit] = useState(100)

  const { data: cameras = [], error: camerasError, isFetching: isFetchingCameras, refetch: refetchCameras } = useQuery({
    queryKey: ['cameras'],
    queryFn:  fetchCameras,
    refetchInterval:      20_000,
    refetchOnReconnect:   true,
    refetchOnWindowFocus: true,
    retry:                3,
  })
  const camMap = Object.fromEntries(cameras.map(c => [c.id, c]))

  const { data: events = [], isFetching, error: eventsError, refetch } = useQuery({
    queryKey:       ['motion', filterCam, limit],
    queryFn:        () => fetchMotionEvents({
      camera_id: filterCam !== 'all' ? cameras.find(c => c.cam_id === filterCam)?.id : undefined,
      active:    undefined,
      limit,
    }),
    refetchInterval:      10_000,
    refetchOnReconnect:   true,
    refetchOnWindowFocus: true,
    retry:                3,
  })

  const activeCount = events.filter(e => effectiveIsActive(e)).length
  const filteredEvents =
    filterActive === 'all'    ? events
    : filterActive === 'active' ? events.filter(e => effectiveIsActive(e))
    :                             events.filter(e => !effectiveIsActive(e))

  return (
    <div className="flex flex-col h-full p-4 lg:p-6 gap-5 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-base font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
              Motion Alerts
            </h1>
            <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
              {activeCount > 0 ? `${activeCount} active right now` : 'No active motion'}
            </p>
          </div>
          {activeCount > 0 && (
            <span className="flex items-center gap-1.5 font-mono text-xs px-2 py-1 rounded-md animate-[pulse-dot_2s_ease-in-out_infinite]"
                  style={{ background: 'oklch(0.62 0.22 25 / 0.1)', border: '1px solid oklch(0.62 0.22 25 / 0.3)', color: 'var(--color-destructive)' }}>
              <Bell size={11} /> {activeCount} ACTIVE
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {(camerasError || eventsError) && (
            <span className="text-[10px] font-mono px-2 py-1 rounded-md"
                  style={{ background: 'oklch(0.62 0.22 25 / 0.1)', border: '1px solid oklch(0.62 0.22 25 / 0.4)', color: 'var(--color-destructive)' }}>
              Network issue — will retry
            </span>
          )}
          <button
            onClick={() => { refetchCameras(); refetch() }}
            className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
            style={{ color: 'var(--color-muted-foreground)', background: 'var(--color-secondary)' }}
          >
            {isFetching || isFetchingCameras ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl p-3 shrink-0"
           style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
        <Filter size={14} className="ml-1" style={{ color: 'var(--color-muted-foreground)' }} />

        <FilterGroup
          label="State"
          value={filterActive}
          onChange={(v) => setFilterActive(v as 'all' | 'active' | 'ended')}
          options={['all', 'active', 'ended'] as const}
        />

        <div className="h-5 w-px" style={{ background: 'var(--color-border)' }} />

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium uppercase tracking-widest"
                style={{ color: 'var(--color-muted-foreground)' }}>Camera</span>
          <select
            value={filterCam}
            onChange={e => setFilterCam(e.target.value)}
            className="rounded-md px-2 py-1 text-xs outline-none"
            style={{
              background: 'oklch(0.28 0.03 260 / 0.6)',
              color: 'var(--color-foreground)',
              boxShadow: '0 0 0 1px var(--color-border)',
            }}
          >
            <option value="all">All cameras</option>
            {cameras.map(c => <option key={c.cam_id} value={c.cam_id}>{c.cam_name ?? c.cam_id}</option>)}
          </select>
        </div>

        <span className="ml-auto text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
          {isFetching ? 'Refreshing...' : `${filteredEvents.length} events`}
        </span>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-hidden rounded-2xl flex flex-col min-h-0"
           style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <BellOff size={28} style={{ color: 'var(--color-dim)' }} />
            <p className="text-sm" style={{ color: 'var(--color-muted-foreground)' }}>No motion events found</p>
          </div>
        ) : (
          <>
            <div className="overflow-y-auto flex-1">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="text-left text-[11px] font-medium uppercase tracking-widest"
                      style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)' }}>
                    <th className="px-4 py-3">Event</th>
                    <th className="px-4 py-3">Camera</th>
                    <th className="px-4 py-3">State</th>
                    <th className="px-4 py-3">Started</th>
                    <th className="px-4 py-3">Ended</th>
                    <th className="px-4 py-3">Duration</th>
                    <th className="px-4 py-3 text-right"></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvents.map(ev => {
                    const cam = camMap[ev.camera_id]
                    const isActive = effectiveIsActive(ev)
                    return (
                      <tr key={ev.id}
                          className="cursor-pointer transition-colors last:border-b-0"
                          style={{ borderBottom: '1px solid var(--color-border)' }}
                          onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)')}
                          onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-start gap-3">
                            <div className={`mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg`}
                                 style={{
                                   background: isActive ? 'oklch(0.78 0.15 75 / 0.15)' : 'var(--color-secondary)',
                                   color: isActive ? 'var(--color-warning)' : 'var(--color-muted-foreground)',
                                   boxShadow: `0 0 0 1px ${isActive ? 'oklch(0.78 0.15 75 / 0.3)' : 'var(--color-border)'}`,
                                 }}>
                              {isActive ? <AlertTriangle size={14} /> : <ScanFace size={14} />}
                            </div>
                            <div className="min-w-0">
                              <div className="font-medium" style={{ color: 'var(--color-foreground)' }}>
                                {isActive ? 'Motion in progress' : 'Motion event'}
                              </div>
                              <div className="mt-0.5 font-mono text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
                                #{ev.id}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs">
                          <div style={{ color: 'var(--color-foreground)' }}>{cam?.cam_id ?? `id:${ev.camera_id}`}</div>
                          {cam?.cam_name && <div style={{ color: 'var(--color-muted-foreground)' }}>{cam.cam_name}</div>}
                        </td>
                        <td className="px-4 py-3"><StatePill active={isActive} /></td>
                        <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
                          {format(new Date(ev.motion_start), 'dd MMM HH:mm:ss')}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
                          {effectiveMotionEnd(ev)
                            ? format(new Date(effectiveMotionEnd(ev) as string), 'HH:mm:ss')
                            : <span style={{ color: 'var(--color-destructive)' }}>—</span>}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--color-muted-foreground)' }}>{dur(ev)}</td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => {
                              const startIso = new Date(ev.motion_start).toISOString()
                              const d        = format(new Date(ev.motion_start), 'yyyy-MM-dd')
                              navigate(`/playback?cam=${cam?.cam_id}&date=${d}&start=${encodeURIComponent(startIso)}`)
                            }}
                            title="Review recording"
                            className="rounded-md p-1.5 transition-colors"
                            style={{ color: 'var(--color-primary)' }}
                          >
                            <ExternalLink size={13} />
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            {events.length >= limit && (
              <div className="px-4 py-2 flex justify-center" style={{ borderTop: '1px solid var(--color-border)' }}>
                <button
                  onClick={() => setLimit(l => l + 100)}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
                  style={{ color: 'var(--color-muted-foreground)', background: 'var(--color-secondary)' }}
                >
                  Load more
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
