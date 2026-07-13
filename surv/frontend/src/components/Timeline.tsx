import { useRef, useEffect, useCallback, useState } from 'react'
import { format } from 'date-fns'
import { type Segment, type MotionEvent } from '../api/client'

const MAIN_HEIGHT = 48
const MINI_HEIGHT = 16
const GAP_THRESHOLD_MS = 10_000

const ZOOM_WINDOWS_MS = [
  24 * 60 * 60 * 1000,
  60 * 60 * 1000,
  15 * 60 * 1000,
  5 * 60 * 1000,
  60 * 1000,
]

const ZOOM_LABELS = ['24h', '1h', '15m', '5m', '1m']

interface Props {
  segments:          Segment[]
  rangeStart:        string
  rangeEnd:          string
  activeSegmentId?:  number
  playbackPosition?: number | null
  motionEvents?:     MotionEvent[]
  onSeek:            (seg: Segment) => void
}

interface HoverInfo {
  x: number
  y: number
  time: number
  segment: Segment | null
}

function dayStartMs(date: string) {
  return new Date(`${date}T00:00:00Z`).getTime()
}

function dayEndMs(date: string) {
  return dayStartMs(date) + 86_400_000
}

function segStart(seg: Segment) {
  return new Date(seg.start).getTime()
}

function segEnd(seg: Segment) {
  if (seg.end) return new Date(seg.end).getTime()
  return segStart(seg) + (seg.duration_seconds ?? 60) * 1000
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function formatTimeMs(ts: number) {
  return format(new Date(ts), 'HH:mm:ss')
}

function formatDuration(seconds: number | null | undefined) {
  if (seconds == null) return '—'
  if (seconds < 60) return `${seconds}s`
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
}

export default function Timeline({
  segments,
  rangeStart,
  rangeEnd,
  activeSegmentId,
  playbackPosition = null,
  motionEvents = [],
  onSeek,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mainCanvasRef = useRef<HTMLCanvasElement>(null)
  const miniCanvasRef = useRef<HTMLCanvasElement>(null)
  const [width, setWidth] = useState(900)
  const [zoomIndex, setZoomIndex] = useState(0)
  const [viewCenter, setViewCenter] = useState<number | null>(null)
  const [hover, setHover] = useState<HoverInfo | null>(null)
  const [isPanning, setIsPanning] = useState(false)
  const panStart = useRef({ x: 0, center: 0 })
  const didPan = useRef(false)

  const rangeStartMs = dayStartMs(rangeStart)
  const rangeEndMs = dayEndMs(rangeEnd)
  const rangeMs = rangeEndMs - rangeStartMs

  const defaultCenter = rangeStartMs + rangeMs / 2
  const center = viewCenter ?? defaultCenter
  const windowMs = zoomIndex === 0 ? rangeMs : Math.min(ZOOM_WINDOWS_MS[zoomIndex], rangeMs)
  const viewStart = zoomIndex === 0
    ? rangeStartMs
    : clamp(center - windowMs / 2, rangeStartMs, Math.max(rangeStartMs, rangeEndMs - windowMs))
  const viewEnd = zoomIndex === 0 ? rangeEndMs : viewStart + windowMs

  const sortedSegments = [...segments].sort((a, b) => segStart(a) - segStart(b))

  useEffect(() => {
    setViewCenter(null)
    setZoomIndex(0)
  }, [rangeStart, rangeEnd])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(entries => {
      const w = Math.floor(entries[0]?.contentRect.width ?? 900)
      if (w > 0) setWidth(w)
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const tsToX = useCallback((ts: number, w: number, vStart: number, vEnd: number) => {
    return ((ts - vStart) / (vEnd - vStart)) * w
  }, [])

  const xToTs = useCallback((x: number, w: number, vStart: number, vEnd: number) => {
    return vStart + (x / w) * (vEnd - vStart)
  }, [])

  const findSegmentAt = useCallback((ts: number) => {
    for (const seg of sortedSegments) {
      const start = segStart(seg)
      const end = segEnd(seg)
      if (ts >= start && ts <= end) return seg
    }
    let best: Segment | null = null
    let bestDist = Infinity
    for (const seg of sortedSegments) {
      const dist = Math.abs(ts - segStart(seg))
      if (dist < bestDist) { bestDist = dist; best = seg }
    }
    return best
  }, [sortedSegments])

  const drawMain = useCallback(() => {
    const canvas = mainCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const W = width
    const H = MAIN_HEIGHT

    ctx.fillStyle = '#080C10'
    ctx.fillRect(0, 0, W, H)

    // Gap shading (no recording)
    ctx.fillStyle = '#0F1318'
    for (let i = 0; i < sortedSegments.length - 1; i++) {
      const gapStart = segEnd(sortedSegments[i])
      const gapEnd = segStart(sortedSegments[i + 1])
      if (gapEnd - gapStart > GAP_THRESHOLD_MS) {
        const x1 = tsToX(gapStart, W, viewStart, viewEnd)
        const x2 = tsToX(gapEnd, W, viewStart, viewEnd)
        if (x2 > 0 && x1 < W) {
          ctx.fillRect(Math.max(0, x1), 0, Math.min(W, x2) - Math.max(0, x1), H)
          // Dashed gap marker
          ctx.strokeStyle = '#374151'
          ctx.setLineDash([3, 3])
          ctx.lineWidth = 1
          const midX = (x1 + x2) / 2
          if (midX >= 0 && midX <= W) {
            ctx.beginPath()
            ctx.moveTo(midX, 4)
            ctx.lineTo(midX, H - 4)
            ctx.stroke()
          }
          ctx.setLineDash([])
        }
      }
    }

    // Hour/minute grid
    const gridStep = windowMs <= 5 * 60 * 1000 ? 60_000
      : windowMs <= 15 * 60 * 1000 ? 5 * 60_000
      : windowMs <= 60 * 60 * 1000 ? 15 * 60_000
      : 60 * 60_000

    ctx.strokeStyle = '#1C2333'
    ctx.lineWidth = 1
    const gridStart = Math.ceil(viewStart / gridStep) * gridStep
    for (let t = gridStart; t <= viewEnd; t += gridStep) {
      const x = Math.round(tsToX(t, W, viewStart, viewEnd))
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, H)
      ctx.stroke()
      ctx.fillStyle = '#374151'
      ctx.font = '9px "JetBrains Mono", monospace'
      ctx.fillText(formatTimeMs(t), x + 3, H - 4)
    }

    // Segments
    for (const seg of sortedSegments) {
      const start = segStart(seg)
      const end = segEnd(seg)
      if (end < viewStart || start > viewEnd) continue
      const xStart = tsToX(start, W, viewStart, viewEnd)
      const xEnd = tsToX(end, W, viewStart, viewEnd)
      const barW = Math.max(xEnd - xStart, 2)
      const active = seg.segment_id === activeSegmentId
      ctx.fillStyle = active ? '#60A5FA' : '#3B82F6'
      ctx.fillRect(xStart, active ? 4 : 8, barW, active ? H - 8 : H - 16)
    }

    // Motion events
    for (const ev of motionEvents) {
      const start = new Date(ev.motion_start).getTime()
      const end = ev.motion_end ? new Date(ev.motion_end).getTime() : start + 30_000
      if (end < viewStart || start > viewEnd) continue
      const xStart = tsToX(start, W, viewStart, viewEnd)
      const xEnd = tsToX(end, W, viewStart, viewEnd)
      ctx.fillStyle = 'rgba(239, 68, 68, 0.55)'
      ctx.fillRect(xStart, 2, Math.max(xEnd - xStart, 2), 4)
    }

    // Playhead
    if (playbackPosition != null && playbackPosition >= viewStart && playbackPosition <= viewEnd) {
      const px = tsToX(playbackPosition, W, viewStart, viewEnd)
      ctx.strokeStyle = '#22C55E'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(px, 0)
      ctx.lineTo(px, H)
      ctx.stroke()
      ctx.fillStyle = '#22C55E'
      ctx.beginPath()
      ctx.moveTo(px - 5, 0)
      ctx.lineTo(px + 5, 0)
      ctx.lineTo(px, 6)
      ctx.closePath()
      ctx.fill()
    }

    // Now line (today only)
    const now = Date.now()
    if (now >= viewStart && now <= viewEnd && now >= rangeStartMs && now <= rangeEndMs) {
      const nowX = tsToX(now, W, viewStart, viewEnd)
      ctx.strokeStyle = '#EF4444'
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.moveTo(nowX, 0)
      ctx.lineTo(nowX, H)
      ctx.stroke()
    }
  }, [
    width, sortedSegments, viewStart, viewEnd, windowMs, activeSegmentId,
    playbackPosition, motionEvents, rangeStartMs, rangeEndMs, tsToX,
  ])

  const drawMini = useCallback(() => {
    const canvas = miniCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const W = width
    const H = MINI_HEIGHT

    ctx.fillStyle = '#060A0E'
    ctx.fillRect(0, 0, W, H)

    for (const seg of sortedSegments) {
      const xStart = tsToX(segStart(seg), W, rangeStartMs, rangeEndMs)
      const xEnd = tsToX(segEnd(seg), W, rangeStartMs, rangeEndMs)
      const active = seg.segment_id === activeSegmentId
      ctx.fillStyle = active ? '#60A5FA' : '#2563EB'
      ctx.fillRect(xStart, 3, Math.max(xEnd - xStart, 1), H - 6)
    }

    for (const ev of motionEvents) {
      const start = new Date(ev.motion_start).getTime()
      const x = tsToX(start, W, rangeStartMs, rangeEndMs)
      ctx.fillStyle = '#EF4444'
      ctx.fillRect(x, 1, 2, 2)
    }

    // Viewport indicator
    const vx1 = tsToX(viewStart, W, rangeStartMs, rangeEndMs)
    const vx2 = tsToX(viewEnd, W, rangeStartMs, rangeEndMs)
    ctx.strokeStyle = 'rgba(255,255,255,0.6)'
    ctx.lineWidth = 1
    ctx.strokeRect(vx1, 0, vx2 - vx1, H)
    ctx.fillStyle = 'rgba(255,255,255,0.08)'
    ctx.fillRect(vx1, 0, vx2 - vx1, H)
  }, [width, sortedSegments, rangeStartMs, rangeEndMs, viewStart, viewEnd, activeSegmentId, motionEvents, tsToX])

  useEffect(() => { drawMain() }, [drawMain])
  useEffect(() => { drawMini() }, [drawMini])

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    const rect = mainCanvasRef.current?.getBoundingClientRect()
    if (!rect) return
    const x = e.clientX - rect.left
    const cursorTs = xToTs(x, width, viewStart, viewEnd)

    if (e.deltaY < 0 && zoomIndex < ZOOM_WINDOWS_MS.length - 1) {
      const next = zoomIndex + 1
      setZoomIndex(next)
      setViewCenter(cursorTs)
    } else if (e.deltaY > 0 && zoomIndex > 0) {
      const next = zoomIndex - 1
      setZoomIndex(next)
      setViewCenter(cursorTs)
    } else if (zoomIndex > 0) {
      const panMs = (e.deltaY / rect.height) * windowMs * 0.5
      setViewCenter(clamp(center - panMs, rangeStartMs + windowMs / 2, rangeEndMs - windowMs / 2))
    }
  }

  const handleMainMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0 || zoomIndex === 0) return
    setIsPanning(true)
    didPan.current = false
    panStart.current = { x: e.clientX, center }
  }

  const handleMainMouseMove = (e: React.MouseEvent) => {
    const rect = mainCanvasRef.current?.getBoundingClientRect()
    if (!rect) return
    const x = e.clientX - rect.left
    const ts = xToTs(x, width, viewStart, viewEnd)

    if (isPanning) {
      if (Math.abs(e.clientX - panStart.current.x) > 3) didPan.current = true
      const dx = e.clientX - panStart.current.x
      const dMs = (dx / width) * windowMs
      setViewCenter(clamp(panStart.current.center - dMs, rangeStartMs + windowMs / 2, rangeEndMs - windowMs / 2))
      return
    }

    setHover({ x: e.clientX, y: e.clientY, time: ts, segment: findSegmentAt(ts) })
  }

  const handleMainMouseUp = () => setIsPanning(false)
  const handleMainMouseLeave = () => { setIsPanning(false); setHover(null) }

  const handleMainClick = (e: React.MouseEvent) => {
    if (didPan.current) return
    const rect = mainCanvasRef.current?.getBoundingClientRect()
    if (!rect) return
    const ts = xToTs(e.clientX - rect.left, width, viewStart, viewEnd)
    const seg = findSegmentAt(ts)
    if (seg) onSeek(seg)
  }

  const handleMiniClick = (e: React.MouseEvent) => {
    const rect = miniCanvasRef.current?.getBoundingClientRect()
    if (!rect) return
    const ts = xToTs(e.clientX - rect.left, width, rangeStartMs, rangeEndMs)
    setViewCenter(clamp(ts, rangeStartMs + windowMs / 2, rangeEndMs - windowMs / 2))
    if (zoomIndex === 0 && rangeMs > ZOOM_WINDOWS_MS[1]) setZoomIndex(1)
  }

  const rangeLabel = rangeStart === rangeEnd
    ? rangeStart
    : `${rangeStart} → ${rangeEnd}`

  return (
    <div ref={containerRef} className="flex flex-col gap-1 select-none">
      <div className="flex justify-between items-center font-mono text-[10px]" style={{ color: 'var(--color-muted-foreground)' }}>
        <span>{formatTimeMs(viewStart)}</span>
        <span className="flex items-center gap-2">
          <span>{sortedSegments.length} segments · {rangeLabel}</span>
          <span className="px-1.5 py-0.5 rounded" style={{ background: 'oklch(0.28 0.03 260 / 0.5)' }}>
            {ZOOM_LABELS[zoomIndex]} · scroll to zoom · drag to pan
          </span>
        </span>
        <span>{formatTimeMs(viewEnd)}</span>
      </div>

      <canvas
        ref={miniCanvasRef}
        width={width}
        height={MINI_HEIGHT}
        onClick={handleMiniClick}
        className="w-full rounded-t border border-border cursor-pointer"
        style={{ height: MINI_HEIGHT }}
        aria-label="Timeline minimap"
      />

      <canvas
        ref={mainCanvasRef}
        width={width}
        height={MAIN_HEIGHT}
        onWheel={handleWheel}
        onMouseDown={handleMainMouseDown}
        onMouseMove={handleMainMouseMove}
        onMouseUp={handleMainMouseUp}
        onMouseLeave={handleMainMouseLeave}
        onClick={handleMainClick}
        className="w-full rounded-b border border-t-0 border-border cursor-grab active:cursor-grabbing"
        style={{ height: MAIN_HEIGHT }}
        aria-label="Recording timeline"
      />

      {sortedSegments.length === 0 && (
        <p className="text-center text-xs py-1" style={{ color: 'var(--color-muted-foreground)' }}>
          No recordings for this date range
        </p>
      )}

      {hover && (
        <div
          className="fixed z-50 pointer-events-none px-2 py-1.5 rounded text-[10px] font-mono shadow-lg"
          style={{
            left: hover.x + 12,
            top: hover.y - 36,
            background: 'oklch(0.18 0.03 260 / 0.95)',
            color: 'var(--color-foreground)',
            boxShadow: '0 0 0 1px var(--color-border)',
          }}
        >
          <div>{format(new Date(hover.time), 'yyyy-MM-dd HH:mm:ss')}</div>
          {hover.segment ? (
            <div style={{ color: 'var(--color-muted-foreground)' }}>
              Segment · {formatDuration(hover.segment.duration_seconds)}
            </div>
          ) : (
            <div style={{ color: 'var(--color-muted-foreground)' }}>No recording</div>
          )}
        </div>
      )}
    </div>
  )
}
