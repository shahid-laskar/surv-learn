import { useState, useRef, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ChevronLeft, ChevronRight, Download, Calendar } from 'lucide-react'
import { fetchCameras, fetchTimeline, type Segment } from '../api/client'
import Timeline from '../components/Timeline'
import StatusBadge from '../components/StatusBadge'

export default function Playback() {
  const [params, setParams] = useSearchParams()
  const [date, setDate]     = useState(format(new Date(), 'yyyy-MM-dd'))
  const [seg, setSeg]       = useState<Segment | null>(null)
  const videoRef            = useRef<HTMLVideoElement>(null)

  const { data: cameras = [] } = useQuery({ queryKey: ['cameras'], queryFn: fetchCameras })
  const selectedId = params.get('cam') ?? ''
  const cam        = cameras.find(c => c.cam_id === selectedId) ?? cameras[0] ?? null

  useEffect(() => {
    if (cam && !selectedId) setParams({ cam: cam.cam_id }, { replace: true })
  }, [cam, selectedId, setParams])

  const { data: timeline, isFetching } = useQuery({
    queryKey: ['timeline', cam?.cam_id, date],
    queryFn:  () => fetchTimeline(cam!.cam_id, date),
    enabled:  !!cam,
  })

  useEffect(() => {
    if (seg && videoRef.current) {
      videoRef.current.src = seg.playback_url
      videoRef.current.load()
      videoRef.current.play().catch(() => {})
    }
  }, [seg])

  const shiftDate = (d: number) => {
    const next = new Date(date); next.setDate(next.getDate() + d)
    setDate(format(next, 'yyyy-MM-dd')); setSeg(null)
  }

  return (
    <div className="flex flex-col h-full p-4 gap-4 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold text-slate-100">Playback</h1>
          <p className="text-xs text-muted mt-0.5">DVR review &amp; recording timeline</p>
        </div>
        <select
          value={cam?.cam_id ?? ''}
          onChange={e => { setParams({ cam: e.target.value }); setSeg(null) }}
          className="bg-surface border border-border rounded px-3 py-2 text-sm
                     text-slate-200 focus:outline-none focus:border-accent/60
                     transition-colors w-52"
        >
          {cameras.map(c => (
            <option key={c.cam_id} value={c.cam_id}>{c.cam_name ?? c.cam_id}</option>
          ))}
        </select>
      </div>

      {!cam ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-muted">No cameras registered.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4 flex-1 min-h-0">
          {/* Player */}
          <div className="relative bg-surface border border-border rounded overflow-hidden"
               style={{ aspectRatio: '16/9', maxHeight: '55vh' }}>
            {seg ? (
              <>
                <video ref={videoRef} controls className="w-full h-full object-contain" />
                <a href={seg.playback_url} download
                   className="absolute top-2 right-2 flex items-center gap-1.5
                              bg-surface/80 border border-border backdrop-blur-sm
                              rounded px-2 py-1 text-xs text-muted hover:text-slate-200 transition-colors">
                  <Download size={11} /> Download
                </a>
              </>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                <Calendar size={28} className="text-dim" />
                <p className="text-sm text-muted">Select a segment from the timeline</p>
              </div>
            )}
          </div>

          {/* Timeline panel */}
          <div className="bg-panel border border-border rounded p-3 flex flex-col gap-3 shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <button onClick={() => shiftDate(-1)}
                        className="p-1.5 text-muted hover:text-slate-200 hover:bg-border rounded transition-colors">
                  <ChevronLeft size={14} />
                </button>
                <input
                  type="date"
                  value={date}
                  max={format(new Date(), 'yyyy-MM-dd')}
                  onChange={e => { setDate(e.target.value); setSeg(null) }}
                  className="bg-surface border border-border rounded px-3 py-1.5 text-xs
                             text-slate-200 focus:outline-none focus:border-accent/60 w-36"
                />
                <button onClick={() => shiftDate(1)}
                        disabled={date >= format(new Date(), 'yyyy-MM-dd')}
                        className="p-1.5 text-muted hover:text-slate-200 hover:bg-border rounded
                                   transition-colors disabled:opacity-30">
                  <ChevronRight size={14} />
                </button>
              </div>
              <div className="flex items-center gap-3">
                {isFetching && <span className="text-xs text-muted animate-pulse">Loading...</span>}
                <StatusBadge online={cam.is_online} />
                <span className="font-mono text-xs text-muted">{cam.cam_id}</span>
              </div>
            </div>
            <Timeline
              segments={timeline?.segments ?? []}
              date={date}
              activeSegmentId={seg?.segment_id}
              onSeek={setSeg}
            />
          </div>

          {/* Segment table */}
          {(timeline?.segments.length ?? 0) > 0 && (
            <div className="bg-panel border border-border rounded overflow-hidden">
              <div className="px-3 py-2 border-b border-border flex justify-between items-center">
                <span className="text-xs font-medium text-slate-300">Segments</span>
                <span className="font-mono text-xs text-muted">{timeline!.total_segments} files</span>
              </div>
              <div className="overflow-y-auto max-h-40">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border text-muted font-mono">
                      <th className="text-left px-3 py-1.5">Start</th>
                      <th className="text-left px-3 py-1.5">Duration</th>
                      <th className="text-right px-3 py-1.5">Save</th>
                    </tr>
                  </thead>
                  <tbody>
                    {timeline!.segments.map(s => (
                      <tr key={s.segment_id}
                          onClick={() => setSeg(s)}
                          className={`border-b border-border/50 cursor-pointer transition-colors
                                      ${seg?.segment_id === s.segment_id ? 'bg-accent/10' : 'hover:bg-border/30'}`}>
                        <td className="px-3 py-1.5 font-mono text-slate-300">
                          {format(new Date(s.start), 'HH:mm:ss')}
                        </td>
                        <td className="px-3 py-1.5 text-muted">{s.duration_seconds ?? '—'}s</td>
                        <td className="px-3 py-1.5 text-right">
                          <a href={s.playback_url} download
                             onClick={e => e.stopPropagation()}
                             className="text-accent hover:text-accent/70 transition-colors">
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
        </div>
      )}
    </div>
  )
}
