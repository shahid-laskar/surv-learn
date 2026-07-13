import { format } from 'date-fns'
import { Film } from 'lucide-react'
import { type Segment } from '../api/client'

interface Props {
  segment: Segment
  active: boolean
  onClick: () => void
  variant?: 'tile' | 'row'
}

function formatDuration(seconds: number | null | undefined) {
  if (seconds == null) return ''
  if (seconds < 60) return `${seconds}s`
  return `${Math.floor(seconds / 60)}m`
}

export default function SegmentThumbnail({ segment, active, onClick, variant = 'tile' }: Props) {
  const start = new Date(segment.start)
  const timeLabel = format(start, 'HH:mm:ss')
  const duration = formatDuration(segment.duration_seconds)

  if (variant === 'row') {
    return (
      <button
        onClick={onClick}
        className="w-full flex items-center gap-2 rounded-lg px-2.5 py-1.5 transition-all text-left"
        style={{
          background: active
            ? 'oklch(0.78 0.14 200 / 0.15)'
            : 'oklch(0.18 0.03 260 / 0.6)',
          boxShadow: active ? '0 0 0 1px var(--color-primary)' : '0 0 0 1px var(--color-border)',
        }}
        title={timeLabel}
        aria-label={`Segment at ${timeLabel}`}
      >
        <Film
          size={12}
          className="shrink-0"
          style={{ color: active ? 'var(--color-primary)' : 'var(--color-muted-foreground)' }}
        />
        <span
          className="font-mono text-[11px] flex-1 truncate"
          style={{ color: active ? 'var(--color-foreground)' : 'var(--color-muted-foreground)' }}
        >
          {timeLabel}
        </span>
        {duration && (
          <span className="font-mono text-[10px] shrink-0" style={{ color: 'var(--color-dim)' }}>
            {duration}
          </span>
        )}
      </button>
    )
  }

  return (
    <button
      onClick={onClick}
      className="relative shrink-0 overflow-hidden rounded-lg transition-all flex flex-col items-center justify-center gap-0.5"
      style={{
        width: 96,
        height: 54,
        background: active
          ? 'oklch(0.78 0.14 200 / 0.15)'
          : 'oklch(0.18 0.03 260 / 0.8)',
        boxShadow: active ? '0 0 0 2px var(--color-primary)' : '0 0 0 1px var(--color-border)',
      }}
      title={timeLabel}
      aria-label={`Segment at ${timeLabel}`}
    >
      <Film
        size={14}
        style={{ color: active ? 'var(--color-primary)' : 'var(--color-muted-foreground)' }}
      />
      <span
        className="font-mono text-[9px]"
        style={{ color: active ? 'var(--color-foreground)' : 'var(--color-muted-foreground)' }}
      >
        {format(start, 'HH:mm')}
      </span>
      {duration && (
        <span className="font-mono text-[8px]" style={{ color: 'var(--color-dim)' }}>
          {duration}
        </span>
      )}
    </button>
  )
}
