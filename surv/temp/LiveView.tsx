import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LayoutGrid, Maximize2, RefreshCw } from 'lucide-react'
import { fetchCameras, fetchHlsUrl, type Camera } from '../api/client'
import HLSPlayer from '../components/HLSPlayer'
import StatusBadge from '../components/StatusBadge'

type GridN = 1 | 2 | 4

function CameraCell({ cam, onExpand }: { cam: Camera; onExpand: () => void }) {
  // Each camera now needs its own token-embedded URL, fetched from FastAPI
  // through Kong rather than constructed client-side. Cached/refetched
  // every 50 minutes since stream tokens expire after 1 hour (server-side).
  const { data: streamInfo } = useQuery({
    queryKey: ['hls-url', cam.cam_id],
    queryFn:  () => fetchHlsUrl(cam.cam_id),
    enabled:  cam.is_online,
    staleTime: 50 * 60 * 1000,
    refetchInterval: 50 * 60 * 1000,
  })

  return (
    <div className="relative bg-card border border-border rounded overflow-hidden
                    group hover:border-accent/40 transition-colors"
         style={{ aspectRatio: '16/9' }}>
      {streamInfo ? (
        <HLSPlayer
          src={streamInfo.hls_url}
          camId={cam.cam_id}
          isOnline={cam.is_online}
          className="absolute inset-0"
        />
      ) : (
        <HLSPlayer
          src=""
          camId={cam.cam_id}
          isOnline={false}
          className="absolute inset-0"
        />
      )}
      {/* Hover bar */}
      <div className="absolute inset-x-0 bottom-0 z-20 flex items-center justify-between
                      px-2 py-1.5 bg-linear-to-t from-surface/90 to-transparent
                      opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        <div>
          <p className="font-mono text-[10px] text-slate-200">{cam.cam_id}</p>
          {cam.cam_name && <p className="text-[9px] text-muted">{cam.cam_name}</p>}
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge online={cam.is_online} />
          <button onClick={onExpand} className="text-muted hover:text-slate-200 transition-colors">
            <Maximize2 size={12} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default function LiveView() {
  const [grid, setGrid]         = useState<GridN>(4)
  const [expanded, setExpanded] = useState<string | null>(null)

  const { data: cameras = [], refetch, isFetching } = useQuery({
    queryKey:       ['cameras'],
    queryFn:        fetchCameras,
    refetchInterval: 20_000,
  })

  const active = cameras.filter(c => c.is_active)
  const shown  = expanded ? active.filter(c => c.cam_id === expanded) : active.slice(0, grid)

  const cols: Record<GridN, string> = {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    4: 'grid-cols-2 xl:grid-cols-4',
  }

  return (
    <div className="flex flex-col h-full p-4 gap-4 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold text-slate-100">Live View</h1>
          <p className="text-xs text-muted mt-0.5">
            {active.filter(c => c.is_online).length} of {active.length} cameras online
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Grid toggle */}
          <div className="flex items-center gap-1 bg-panel border border-border rounded p-1">
            {([1, 2, 4] as GridN[]).map(n => (
              <button
                key={n}
                onClick={() => { setGrid(n); setExpanded(null) }}
                className={`px-2 py-1 rounded font-mono text-xs transition-colors
                            ${grid === n ? 'bg-accent/20 text-accent' : 'text-muted hover:text-slate-200'}`}
              >
                {n === 1 ? '1×1' : n === 2 ? '2×2' : '4×4'}
              </button>
            ))}
          </div>
          {expanded && (
            <button onClick={() => setExpanded(null)}
                    className="px-3 py-1.5 text-muted hover:text-slate-200 text-xs font-medium rounded hover:bg-border transition-colors">
              Show all
            </button>
          )}
          <button onClick={() => refetch()}
                  className="p-1.5 text-muted hover:text-slate-200 rounded hover:bg-border transition-colors">
            <RefreshCw size={13} className={isFetching ? 'animate-spin text-accent' : ''} />
          </button>
        </div>
      </div>

      {/* Grid */}
      {active.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <LayoutGrid size={36} className="text-dim" />
          <p className="text-sm text-slate-300">No cameras registered</p>
          <p className="text-xs text-muted">Add cameras in the Cameras tab</p>
        </div>
      ) : (
        <div className={`grid ${cols[grid]} gap-2 flex-1 overflow-hidden`}>
          {shown.map(cam => (
            <CameraCell
              key={cam.cam_id}
              cam={cam}
              onExpand={() => setExpanded(expanded === cam.cam_id ? null : cam.cam_id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
