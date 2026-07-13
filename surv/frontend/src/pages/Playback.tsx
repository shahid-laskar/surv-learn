import { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useQueries } from '@tanstack/react-query'
import { format, eachDayOfInterval, parseISO, isAfter, min as minDate } from 'date-fns'
import { ChevronLeft, ChevronRight, Download, Calendar, Film, HardDrive, PanelRightClose, PanelRightOpen } from 'lucide-react'
import { fetchCameras, fetchTimeline, fetchMotionEvents, type Segment } from '../api/client'
import Timeline from '../components/Timeline'
import SegmentThumbnail from '../components/SegmentThumbnail'
import HLSPlayer, { type HLSPlayerRef } from '../components/HLSPlayer'
import { clampPlaybackSpeed } from '../lib/videoPlayback'

const inputStyle = {
  background: 'oklch(0.28 0.03 260 / 0.5)',
  color: 'var(--color-foreground)',
  boxShadow: '0 0 0 1px var(--color-border)',
} as React.CSSProperties

function formatFileSize(bytes: number | null | undefined) {
  if (bytes == null || bytes === 0) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function inferCodec(url: string) {
  const path = url.split('?')[0].toLowerCase()
  if (path.endsWith('.mp4')) return 'H.264 / MP4'
  if (path.endsWith('.ts')) return 'MPEG-TS'
  if (path.endsWith('.webm')) return 'VP8/VP9 / WebM'
  if (path.endsWith('.mkv')) return 'H.264 / MKV'
  return 'Unknown'
}

function enumerateDates(start: string, end: string): string[] {
  const startDate = parseISO(`${start}T00:00:00Z`)
  const endDate = parseISO(`${end}T00:00:00Z`)
  if (isAfter(startDate, endDate)) return [start]
  return eachDayOfInterval({ start: startDate, end: endDate }).map(d => format(d, 'yyyy-MM-dd'))
}

export default function Playback() {
  const [params, setParams] = useSearchParams()
  const today = format(new Date(), 'yyyy-MM-dd')
  const [dateStart, setDateStart] = useState(today)
  const [dateEnd, setDateEnd]     = useState(today)
  const [seg, setSeg]             = useState<Segment | null>(null)
  const [playbackPosition, setPlaybackPosition] = useState<number | null>(null)
  const [exporting, setExporting] = useState(false)
  const [panelOpen, setPanelOpen] = useState(() => localStorage.getItem('playback-panel') !== 'closed')
  const [playbackRate, setPlaybackRate] = useState(() => {
    const saved = parseFloat(localStorage.getItem('playback-rate') ?? '1')
    return clampPlaybackSpeed(Number.isFinite(saved) ? saved : 1)
  })
  const playerRef = useRef<HLSPlayerRef>(null)
  const thumbStripRef = useRef<HTMLDivElement>(null)

  const { data: cameras = [] } = useQuery({ queryKey: ['cameras'], queryFn: fetchCameras })
  const selectedId = params.get('cam') ?? ''
  const startHint  = params.get('start') ?? ''
  const cam        = cameras.find(c => c.cam_id === selectedId) ?? cameras[0] ?? null

  useEffect(() => {
    if (cam && !selectedId) setParams({ cam: cam.cam_id }, { replace: true })
  }, [cam, selectedId, setParams])

  const dates = useMemo(() => enumerateDates(dateStart, dateEnd), [dateStart, dateEnd])

  const timelineQueries = useQueries({
    queries: dates.map(date => ({
      queryKey: ['timeline', cam?.cam_id, date],
      queryFn:  () => fetchTimeline(cam!.cam_id, date),
      enabled:  !!cam,
      staleTime: 60_000,
    })),
  })

  const isFetching = timelineQueries.some(q => q.isFetching)

  const allSegments: Segment[] = useMemo(() => {
    const merged: Segment[] = []
    for (const q of timelineQueries) {
      if (q.data?.segments) merged.push(...q.data.segments)
    }
    const seen = new Set<number>()
    return merged.filter(s => {
      if (seen.has(s.segment_id)) return false
      seen.add(s.segment_id)
      return true
    })
  }, [timelineQueries])

  const chronologicalSegments = useMemo(
    () => [...allSegments].sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime()),
    [allSegments],
  )

  const segRef = useRef(seg)
  const segmentsRef = useRef(chronologicalSegments)
  segRef.current = seg
  segmentsRef.current = chronologicalSegments

  const displaySegments = useMemo(
    () => [...chronologicalSegments].reverse(),
    [chronologicalSegments],
  )

  const totalSegments = timelineQueries.reduce((n, q) => n + (q.data?.total_segments ?? 0), 0)

  const rangeStartMs = new Date(`${dateStart}T00:00:00Z`).getTime()
  const rangeEndMs = new Date(`${dateEnd}T00:00:00Z`).getTime() + 86_400_000

  const { data: motionEvents = [] } = useQuery({
    queryKey: ['motion-playback', cam?.id, dateStart, dateEnd],
    queryFn:  () => fetchMotionEvents({ camera_id: cam!.id, limit: 500 }),
    enabled:  !!cam,
    staleTime: 60_000,
  })

  const filteredMotion = useMemo(
    () => motionEvents.filter(ev => {
      const t = new Date(ev.motion_start).getTime()
      return t >= rangeStartMs && t < rangeEndMs
    }),
    [motionEvents, rangeStartMs, rangeEndMs],
  )

  useEffect(() => {
    if (!chronologicalSegments.length || !startHint || seg) return
    const target = new Date(startHint).getTime()
    if (Number.isNaN(target)) return

    let best: Segment | null = null
    let bestScore = Number.POSITIVE_INFINITY

    for (const s of chronologicalSegments) {
      const startTs = new Date(s.start).getTime()
      const endTs   = s.end ? new Date(s.end).getTime() : startTs
      if (Number.isNaN(startTs)) continue

      if (startTs <= target && target <= endTs) { best = s; break }
      const score = Math.abs(startTs - target)
      if (score < bestScore) { bestScore = score; best = s }
    }

    if (best) setSeg(best)
  }, [chronologicalSegments, startHint, seg])

  useEffect(() => {
    if (!seg) {
      setPlaybackPosition(null)
      return
    }

    let cleanup: (() => void) | undefined
    const attach = () => {
      const video = playerRef.current?.video
      if (!video) return false
      const onTime = () => {
        setPlaybackPosition(new Date(seg.start).getTime() + video.currentTime * 1000)
      }
      video.addEventListener('timeupdate', onTime)
      onTime()
      cleanup = () => video.removeEventListener('timeupdate', onTime)
      return true
    }

    if (!attach()) {
      const id = window.setInterval(() => { if (attach()) clearInterval(id) }, 150)
      return () => { clearInterval(id); cleanup?.() }
    }
    return () => cleanup?.()
  }, [seg])

  useEffect(() => {
    if (!seg || !thumbStripRef.current) return
    const el = thumbStripRef.current.querySelector(`[data-seg="${seg.segment_id}"]`)
    el?.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
  }, [seg])

  const handleEnded = useCallback(() => {
    const current = segRef.current
    if (!current) return
    const segments = segmentsRef.current
    const idx = segments.findIndex(s => s.segment_id === current.segment_id)
    if (idx >= 0 && idx < segments.length - 1) {
      setSeg(segments[idx + 1])
    }
  }, [])

  const togglePanel = () => {
    setPanelOpen(open => {
      const next = !open
      localStorage.setItem('playback-panel', next ? 'open' : 'closed')
      return next
    })
  }

  const handlePlaybackRateChange = useCallback((rate: number) => {
    const clamped = clampPlaybackSpeed(rate)
    setPlaybackRate(clamped)
    localStorage.setItem('playback-rate', String(clamped))
  }, [])

  const shiftRange = (days: number) => {
    const s = new Date(`${dateStart}T00:00:00Z`)
    const e = new Date(`${dateEnd}T00:00:00Z`)
    s.setUTCDate(s.getUTCDate() + days)
    e.setUTCDate(e.getUTCDate() + days)
    const todayDate = parseISO(`${today}T00:00:00Z`)
    if (isAfter(e, todayDate)) return
    setDateStart(format(s, 'yyyy-MM-dd'))
    setDateEnd(format(minDate([e, todayDate]), 'yyyy-MM-dd'))
    setSeg(null)
  }

  const handleDateStartChange = (value: string) => {
    setDateStart(value)
    if (value > dateEnd) setDateEnd(value)
    setSeg(null)
  }

  const handleDateEndChange = (value: string) => {
    const clamped = value > today ? today : value
    setDateEnd(clamped)
    if (clamped < dateStart) setDateStart(clamped)
    setSeg(null)
  }

  const exportAllSegments = async () => {
    if (!cam || !chronologicalSegments.length) return
    setExporting(true)
    try {
      for (const s of chronologicalSegments) {
        if (!s.playback_url) continue
        const a = document.createElement('a')
        a.href = s.playback_url
        a.download = `${cam.cam_id}-${format(new Date(s.start), 'yyyyMMdd-HHmmss')}.mp4`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        await new Promise(r => setTimeout(r, 400))
      }
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="flex flex-col h-full p-4 lg:p-6 gap-4 animate-[fade-in_0.2s_ease-out] min-h-0 overflow-hidden">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold"
              style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            Playback
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
            DVR review & recording timeline
          </p>
        </div>
        <select
          value={cam?.cam_id ?? ''}
          onChange={e => { setParams({ cam: e.target.value }); setSeg(null) }}
          className="rounded-lg px-3 py-2 text-sm outline-none transition-all w-52"
          style={inputStyle}
        >
          {cameras.map(c => (
            <option key={c.cam_id} value={c.cam_id}>{c.cam_name ?? c.cam_id}</option>
          ))}
        </select>
      </div>

      {!cam ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm" style={{ color: 'var(--color-muted-foreground)' }}>No cameras registered.</p>
        </div>
      ) : (
        <div className="flex flex-1 min-h-0 gap-4 flex-col lg:flex-row">
          {/* Main column: video + timeline */}
          <div className="flex flex-col flex-1 min-h-0 min-w-0 gap-3">
            <div className="relative flex-1 min-h-[200px] overflow-hidden rounded-xl bg-black"
                 style={{ boxShadow: '0 0 0 1px var(--color-border)' }}>
              {seg ? (
                <>
                  <HLSPlayer
                    ref={playerRef}
                    src={seg.playback_url}
                    camId={cam.cam_id}
                    isOnline={true}
                    showControls={true}
                    autoPlay={true}
                    muted={false}
                    forceNative={true}
                    playbackRate={playbackRate}
                    onPlaybackRateChange={handlePlaybackRateChange}
                    onEnded={handleEnded}
                    className="absolute inset-0"
                  />
                  <button
                    type="button"
                    onClick={togglePanel}
                    className="absolute top-3 left-3 flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors z-30 pointer-events-auto"
                    style={{
                      background: 'rgba(0,0,0,0.6)',
                      color: 'white',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 0 0 1px rgba(255,255,255,0.1)',
                    }}
                    aria-label={panelOpen ? 'Hide side panel' : 'Show side panel'}
                    title={panelOpen ? 'Hide panel' : 'Show panel'}
                  >
                    {panelOpen ? <PanelRightClose size={13} /> : <PanelRightOpen size={13} />}
                    <span className="hidden sm:inline">{panelOpen ? 'Hide panel' : 'Show panel'}</span>
                  </button>
                  <a
                    href={seg.playback_url}
                    download
                    className="absolute top-3 right-3 flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors z-30 pointer-events-auto"
                    style={{
                      background: 'rgba(0,0,0,0.6)',
                      color: 'white',
                      backdropFilter: 'blur(8px)',
                      boxShadow: '0 0 0 1px rgba(255,255,255,0.1)',
                    }}
                  >
                    <Download size={11} /> Download
                  </a>
                </>
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                  <Calendar size={28} style={{ color: 'var(--color-dim)' }} />
                  <p className="text-sm" style={{ color: 'var(--color-muted-foreground)' }}>
                    Select a segment from the timeline
                  </p>
                </div>
              )}
            </div>

            <div className="rounded-2xl p-4 flex flex-col gap-3 shrink-0"
                 style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <button onClick={() => shiftRange(-1)}
                          className="p-1.5 rounded-lg transition-colors"
                          style={{ color: 'var(--color-muted-foreground)' }}
                          aria-label="Previous day">
                    <ChevronLeft size={14} />
                  </button>
                  <input
                    type="date"
                    value={dateStart}
                    max={today}
                    onChange={e => handleDateStartChange(e.target.value)}
                    className="rounded-lg px-3 py-1.5 text-xs outline-none w-36"
                    style={inputStyle}
                    aria-label="Start date"
                  />
                  <span className="text-xs" style={{ color: 'var(--color-muted-foreground)' }}>to</span>
                  <input
                    type="date"
                    value={dateEnd}
                    max={today}
                    min={dateStart}
                    onChange={e => handleDateEndChange(e.target.value)}
                    className="rounded-lg px-3 py-1.5 text-xs outline-none w-36"
                    style={inputStyle}
                    aria-label="End date"
                  />
                  <button onClick={() => shiftRange(1)}
                          disabled={dateEnd >= today}
                          className="p-1.5 rounded-lg transition-colors disabled:opacity-30"
                          style={{ color: 'var(--color-muted-foreground)' }}
                          aria-label="Next day">
                    <ChevronRight size={14} />
                  </button>
                </div>
                <div className="flex items-center gap-3">
                  {isFetching && (
                    <span className="text-xs animate-pulse" style={{ color: 'var(--color-muted-foreground)' }}>
                      Loading...
                    </span>
                  )}
                  <div className="flex items-center gap-2">
                    <span className="size-1.5 rounded-full"
                          style={{ background: cam.is_online ? 'var(--color-success)' : 'var(--color-destructive)' }} />
                    <span className="font-mono text-xs" style={{ color: 'var(--color-muted-foreground)' }}>{cam.cam_id}</span>
                  </div>
                </div>
              </div>
              <Timeline
                segments={chronologicalSegments}
                rangeStart={dateStart}
                rangeEnd={dateEnd}
                activeSegmentId={seg?.segment_id}
                playbackPosition={playbackPosition}
                motionEvents={filteredMotion}
                onSeek={setSeg}
              />
            </div>
          </div>

          {/* Right panel: metadata, clips, segment list */}
          {panelOpen && (
          <aside
            className="flex flex-col gap-3 w-full lg:w-72 xl:w-80 shrink-0 min-h-0 lg:max-h-full overflow-hidden"
            style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)', borderRadius: '1rem' }}
          >
            <div className="p-4 flex flex-col gap-3 shrink-0"
                 style={{ borderBottom: '1px solid var(--color-border)' }}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium" style={{ color: 'var(--color-foreground)' }}>
                  {seg ? 'Now playing' : 'No selection'}
                </span>
                {chronologicalSegments.length > 0 && (
                  <button
                    onClick={() => void exportAllSegments()}
                    disabled={exporting}
                    className="flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-medium transition-colors disabled:opacity-50"
                    style={{
                      background: 'oklch(0.28 0.03 260 / 0.5)',
                      color: 'var(--color-primary)',
                      boxShadow: '0 0 0 1px var(--color-border)',
                    }}
                  >
                    <Download size={10} />
                    {exporting ? '…' : 'Export all'}
                  </button>
                )}
              </div>

              {seg ? (
                <div className="grid grid-cols-2 gap-x-3 gap-y-2">
                  <MetadataItem icon={<Film size={12} />} label="Start"
                    value={format(new Date(seg.start), 'HH:mm:ss')} compact />
                  <MetadataItem icon={<Film size={12} />} label="End"
                    value={seg.end ? format(new Date(seg.end), 'HH:mm:ss') : '—'} compact />
                  <MetadataItem icon={<Film size={12} />} label="Duration"
                    value={seg.duration_seconds != null ? `${seg.duration_seconds}s` : '—'} compact />
                  <MetadataItem icon={<HardDrive size={12} />} label="Size"
                    value={formatFileSize(seg.file_size_bytes)} compact />
                  <div className="col-span-2">
                    <MetadataItem icon={<Film size={12} />} label="Codec"
                      value={inferCodec(seg.playback_url)} compact />
                  </div>
                </div>
              ) : (
                <p className="text-[11px]" style={{ color: 'var(--color-muted-foreground)' }}>
                  Click the timeline or pick a clip below to start playback.
                </p>
              )}
            </div>

            {chronologicalSegments.length > 0 && (
              <div className="px-4 shrink-0">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-medium" style={{ color: 'var(--color-foreground)' }}>
                    Clips
                  </span>
                  <span className="text-[10px] font-mono" style={{ color: 'var(--color-muted-foreground)' }}>
                    {chronologicalSegments.length}
                  </span>
                </div>
                <div
                  ref={thumbStripRef}
                  className="flex gap-2 overflow-x-auto pb-2 lg:flex-col lg:overflow-x-hidden lg:overflow-y-auto lg:max-h-32 scroll-smooth"
                  style={{ scrollbarWidth: 'thin' }}
                >
                  {chronologicalSegments.map(s => (
                    <div key={s.segment_id} data-seg={s.segment_id} className="lg:w-full shrink-0">
                      <div className="lg:hidden">
                        <SegmentThumbnail
                          segment={s}
                          active={seg?.segment_id === s.segment_id}
                          onClick={() => setSeg(s)}
                          variant="tile"
                        />
                      </div>
                      <div className="hidden lg:block">
                        <SegmentThumbnail
                          segment={s}
                          active={seg?.segment_id === s.segment_id}
                          onClick={() => setSeg(s)}
                          variant="row"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {allSegments.length > 0 && (
              <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
                <div className="px-4 py-2 flex justify-between items-center shrink-0"
                     style={{ borderTop: '1px solid var(--color-border)' }}>
                  <span className="text-[11px] font-medium" style={{ color: 'var(--color-foreground)' }}>Segments</span>
                  <span className="font-mono text-[10px]" style={{ color: 'var(--color-muted-foreground)' }}>
                    {totalSegments}
                  </span>
                </div>
                <div className="overflow-y-auto flex-1 min-h-0">
                  <table className="w-full text-xs border-collapse">
                    <thead className="sticky top-0 z-10"
                           style={{ background: 'oklch(0.22 0.035 260)' }}>
                      <tr className="text-[10px] font-medium uppercase tracking-widest"
                          style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)' }}>
                        <th className="text-left px-3 py-1.5">Time</th>
                        <th className="text-left px-2 py-1.5">Dur</th>
                        <th className="text-right px-3 py-1.5"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {displaySegments.map(s => (
                        <tr key={s.segment_id}
                            onClick={() => setSeg(s)}
                            className="cursor-pointer transition-colors"
                            style={{
                              borderBottom: '1px solid var(--color-border)',
                              background: seg?.segment_id === s.segment_id ? 'oklch(0.78 0.14 200 / 0.08)' : undefined,
                            }}
                            onMouseOver={e => { if (seg?.segment_id !== s.segment_id) e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)' }}
                            onMouseOut={e => { if (seg?.segment_id !== s.segment_id) e.currentTarget.style.background = 'transparent' }}>
                          <td className="px-3 py-1.5 font-mono text-[11px]" style={{ color: 'var(--color-foreground)' }}>
                            {format(new Date(s.start), 'HH:mm:ss')}
                          </td>
                          <td className="px-2 py-1.5 text-[11px]" style={{ color: 'var(--color-muted-foreground)' }}>
                            {s.duration_seconds ?? '—'}s
                          </td>
                          <td className="px-3 py-1.5 text-right">
                            <a href={s.playback_url} download
                               onClick={e => e.stopPropagation()}
                               className="transition-colors"
                               style={{ color: 'var(--color-primary)' }}
                               aria-label="Download segment">
                              <Download size={11} />
                            </a>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </aside>
          )}
        </div>
      )}
    </div>
  )
}

function MetadataItem({
  icon, label, value, compact = false,
}: {
  icon: React.ReactNode
  label: string
  value: string
  compact?: boolean
}) {
  return (
    <div className="flex items-center gap-1.5">
      <span style={{ color: 'var(--color-muted-foreground)' }}>{icon}</span>
      <div className="min-w-0">
        <div className="text-[9px] uppercase tracking-wider truncate" style={{ color: 'var(--color-muted-foreground)' }}>
          {label}
        </div>
        <div
          className={`font-mono truncate ${compact ? 'text-[11px]' : 'text-xs'}`}
          style={{ color: 'var(--color-foreground)' }}
        >
          {value}
        </div>
      </div>
    </div>
  )
}
