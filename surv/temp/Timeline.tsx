import { useRef, useEffect, useCallback } from 'react'
import { type Segment } from '../api/client'

interface Props {
  segments:        Segment[]
  date:            string
  activeSegmentId?: number
  onSeek:          (seg: Segment) => void
}

export default function Timeline({ segments, date, activeSegmentId, onSeek }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const DAY_START = new Date(`${date}T00:00:00Z`).getTime()
  const DAY_MS    = 86_400_000

  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    const W   = canvas.width
    const H   = canvas.height

    // Background
    ctx.fillStyle = '#080C10'
    ctx.fillRect(0, 0, W, H)

    // Hour grid
    ctx.strokeStyle = '#1C2333'
    ctx.lineWidth   = 1
    for (let h = 0; h <= 24; h++) {
      const x = Math.round((h / 24) * W)
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke()
      if (h % 6 === 0) {
        ctx.fillStyle = '#374151'
        ctx.font      = '9px "JetBrains Mono", monospace'
        ctx.fillText(`${String(h).padStart(2, '0')}:00`, x + 3, H - 4)
      }
    }

    // Segments
    for (const seg of segments) {
      const start  = new Date(seg.start).getTime()
      const end    = seg.end
        ? new Date(seg.end).getTime()
        : start + (seg.duration_seconds ?? 60) * 1000
      const xStart = ((start - DAY_START) / DAY_MS) * W
      const xEnd   = ((end   - DAY_START) / DAY_MS) * W
      const barW   = Math.max(xEnd - xStart, 2)
      const active = seg.segment_id === activeSegmentId

      ctx.fillStyle = active ? '#60A5FA' : '#3B82F6'
      ctx.fillRect(xStart, active ? 4 : 8, barW, active ? H - 8 : H - 16)
    }

    // Now line
    const nowX = ((Date.now() - DAY_START) / DAY_MS) * W
    if (nowX >= 0 && nowX <= W) {
      ctx.strokeStyle = '#EF4444'
      ctx.lineWidth   = 1.5
      ctx.beginPath(); ctx.moveTo(nowX, 0); ctx.lineTo(nowX, H); ctx.stroke()
    }
  }, [segments, activeSegmentId, DAY_START, DAY_MS])

  useEffect(() => { draw() }, [draw])

  const handleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas || !segments.length) return
    const ratio   = (e.clientX - canvas.getBoundingClientRect().left) / canvas.offsetWidth
    const clickTs = DAY_START + ratio * DAY_MS

    // Prefer a segment whose range contains the click
    for (const seg of segments) {
      const start = new Date(seg.start).getTime()
      const end   = seg.end ? new Date(seg.end).getTime() : start + 60_000
      if (clickTs >= start && clickTs <= end) { onSeek(seg); return }
    }
    // Fall back to nearest
    let best: Segment | null = null, bestDist = Infinity
    for (const seg of segments) {
      const dist = Math.abs(clickTs - new Date(seg.start).getTime())
      if (dist < bestDist) { bestDist = dist; best = seg }
    }
    if (best) onSeek(best)
  }, [segments, DAY_START, DAY_MS, onSeek])

  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between font-mono text-[10px] text-muted">
        <span>00:00</span>
        <span className="text-slate-400">{segments.length} segments · {date}</span>
        <span>24:00</span>
      </div>
      <canvas
        ref={canvasRef}
        width={900}
        height={40}
        onClick={handleClick}
        className="w-full h-10 rounded border border-border cursor-pointer"
      />
      {segments.length === 0 && (
        <p className="text-center text-xs text-muted py-1">No recordings for this date</p>
      )}
    </div>
  )
}
