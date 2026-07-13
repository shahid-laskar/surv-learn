import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  LayoutGrid, Maximize2, RefreshCw, Minimize2,
  ChevronUp, ChevronDown, ChevronLeft, ChevronRight,
  Camera as CameraIcon, Link, PictureInPicture, Play,
} from 'lucide-react'
import { fetchCameras, fetchHlsUrl, type Camera } from '../api/client'
import HLSPlayer, { type HLSPlayerRef } from '../components/HLSPlayer'

interface ContextMenuState {
  x: number
  y: number
}

type GridN = 1 | 2 | 4

// ── Status helpers ─────────────────────────────────────────
function StatusDot({ online }: { online: boolean }) {
  return (
    <span className="relative flex size-2">
      <span
        className="absolute inline-flex h-full w-full rounded-full opacity-70 animate-ping"
        style={{ background: online ? 'oklch(0.72 0.17 150 / 0.7)' : 'oklch(0.62 0.22 25 / 0.7)' }}
      />
      <span
        className="relative size-2 rounded-full"
        style={{ background: online ? 'var(--color-success)' : 'var(--color-destructive)' }}
      />
    </span>
  )
}

// ── KPI card ───────────────────────────────────────────────
function KpiCard({ label, value, sub, tone }: { label: string; value: string; sub: string; tone: 'success' | 'warning' | 'muted' }) {
  const subColor = tone === 'success' ? 'var(--color-success)' : tone === 'warning' ? 'var(--color-warning)' : 'var(--color-muted-foreground)'
  return (
    <div className="rounded-xl p-4" style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
      <div className="mb-1 text-xs font-medium" style={{ color: 'var(--color-muted-foreground)' }}>{label}</div>
      <div className="text-2xl font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>{value}</div>
      <div className="mt-1 text-xs font-medium" style={{ color: subColor }}>{sub}</div>
    </div>
  )
}

// ── PTZ button ────────────────────────────────────────────
function PtzButton({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex size-9 items-center justify-center rounded-lg transition-colors"
      style={{ background: 'rgba(0,0,0,0.6)', color: 'white', boxShadow: '0 0 0 1px rgba(255,255,255,0.1)', backdropFilter: 'blur(8px)' }}
      onMouseOver={e => { e.currentTarget.style.background = 'var(--color-primary)'; e.currentTarget.style.color = 'var(--color-primary-foreground)' }}
      onMouseOut={e => { e.currentTarget.style.background = 'rgba(0,0,0,0.6)'; e.currentTarget.style.color = 'white' }}
    >
      {children}
    </button>
  )
}

// ── Featured feed ─────────────────────────────────────────
function FeaturedFeed({ cam, onCollapse }: { cam: Camera; onCollapse: () => void }) {
  const navigate = useNavigate()
  const containerRef = useRef<HTMLDivElement>(null)
  const playerRef = useRef<HLSPlayerRef>(null)
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null)

  const { data: streamInfo, refetch: refetchStream } = useQuery({
    queryKey: ['hls-url', cam.cam_id],
    queryFn:  () => fetchHlsUrl(cam.cam_id),
    enabled:  cam.is_online,
    staleTime: 45 * 60 * 1000,
    refetchInterval: 45 * 60 * 1000,
  })

  const closeContextMenu = useCallback(() => setContextMenu(null), [])

  useEffect(() => {
    if (!contextMenu) return
    const onDismiss = () => closeContextMenu()
    window.addEventListener('click', onDismiss)
    window.addEventListener('scroll', onDismiss, true)
    return () => {
      window.removeEventListener('click', onDismiss)
      window.removeEventListener('scroll', onDismiss, true)
    }
  }, [contextMenu, closeContextMenu])

  const copyStreamUrl = async () => {
    const url = streamInfo?.hls_url ?? playerRef.current?.getStreamUrl() ?? ''
    if (!url) return
    await navigator.clipboard.writeText(url).catch(() => {})
    closeContextMenu()
  }

  return (
    <div
      ref={containerRef}
      className="relative overflow-hidden rounded-xl bg-black"
      style={{ aspectRatio: '16/9', boxShadow: '0 0 0 1px var(--color-border)' }}
      onContextMenu={(e) => {
        e.preventDefault()
        setContextMenu({ x: e.clientX, y: e.clientY })
      }}
    >
      <HLSPlayer
        ref={playerRef}
        src={streamInfo?.hls_url ?? ''}
        camId={cam.cam_id}
        isOnline={cam.is_online}
        className="absolute inset-0"
        onNeedsRefresh={refetchStream}
        muted={true}
        autoPlay={true}
        showControls={true}
        isLive={true}
      />

      {/* Top overlay */}
      <div className="absolute inset-x-0 top-0 flex items-start justify-between p-4 z-20 pointer-events-none">
        <div className="flex items-center gap-2 rounded-lg px-3 py-1.5 pointer-events-auto"
             style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(8px)', boxShadow: '0 0 0 1px rgba(255,255,255,0.1)' }}>
          <StatusDot online={cam.is_online} />
          <span className="text-xs font-semibold uppercase tracking-wide text-white">{cam.cam_id} · {cam.cam_ip}</span>
        </div>
        <div className="flex items-center gap-2 pointer-events-auto">
          {cam.cam_name && (
            <span className="rounded-md px-2 py-1 font-mono text-[10px] text-white/80"
                  style={{ background: 'rgba(0,0,0,0.5)', boxShadow: '0 0 0 1px rgba(255,255,255,0.1)' }}>
              {cam.cam_name}
            </span>
          )}
          <button onClick={onCollapse} className="rounded-lg p-1.5 bg-black/50 hover:bg-black/80 text-white transition-colors"
                  style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.1)' }}>
            <Minimize2 size={14} />
          </button>
        </div>
      </div>

      {/* PTZ pad */}
      <div className="absolute bottom-24 right-4 grid grid-cols-3 gap-1.5 z-20">
        <span /><PtzButton onClick={() => console.log('PTZ UP')}><ChevronUp size={16} /></PtzButton><span />
        <PtzButton onClick={() => console.log('PTZ LEFT')}><ChevronLeft size={16} /></PtzButton>
        <PtzButton onClick={() => console.log('PTZ HOME')}><div className="size-2 rounded-full bg-current" /></PtzButton>
        <PtzButton onClick={() => console.log('PTZ RIGHT')}><ChevronRight size={16} /></PtzButton>
        <span /><PtzButton onClick={() => console.log('PTZ DOWN')}><ChevronDown size={16} /></PtzButton><span />
      </div>

      {contextMenu && (
        <div
          className="fixed z-50 min-w-44 rounded-lg py-1 shadow-xl backdrop-blur-sm"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
            background: 'oklch(0.18 0.03 260 / 0.95)',
            boxShadow: '0 0 0 1px var(--color-border)',
          }}
          onClick={e => e.stopPropagation()}
        >
          <ContextMenuItem
            icon={<CameraIcon size={14} />}
            label="Snapshot"
            onClick={() => { playerRef.current?.snapshot(); closeContextMenu() }}
          />
          <ContextMenuItem
            icon={<Link size={14} />}
            label="Copy stream URL"
            onClick={() => void copyStreamUrl()}
          />
          <ContextMenuItem
            icon={<PictureInPicture size={14} />}
            label="Picture in Picture"
            onClick={() => { playerRef.current?.togglePip(); closeContextMenu() }}
          />
          <ContextMenuItem
            icon={<Play size={14} />}
            label="View in Playback"
            onClick={() => { navigate(`/playback?cam=${cam.cam_id}`); closeContextMenu() }}
          />
        </div>
      )}
    </div>
  )
}

function ContextMenuItem({ icon, label, onClick }: { icon: React.ReactNode; label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-white hover:bg-white/10 transition-colors"
    >
      {icon}
      <span>{label}</span>
    </button>
  )
}

// ── Mini tile ─────────────────────────────────────────────
function MiniTile({ cam, selected, onSelect }: { cam: Camera; selected: boolean; onSelect: () => void }) {
  const { data: streamInfo } = useQuery({
    queryKey: ['hls-url', cam.cam_id],
    queryFn:  () => fetchHlsUrl(cam.cam_id),
    enabled:  cam.is_online,
    staleTime: 45 * 60 * 1000,
    refetchInterval: 45 * 60 * 1000,
  })

  return (
    <button
      onClick={onSelect}
      className="group relative overflow-hidden rounded-xl bg-black text-left transition-all"
      style={{ aspectRatio: '16/9', boxShadow: selected ? '0 0 0 1.5px var(--color-primary)' : '0 0 0 1px var(--color-border)' }}
    >
      <HLSPlayer src={streamInfo?.hls_url ?? ''} camId={cam.cam_id} isOnline={cam.is_online} className="absolute inset-0" muted={true} autoPlay={true} />

      <div className="absolute inset-x-0 top-0 z-20 flex items-center justify-between p-2 pointer-events-none">
        <div className="flex items-center gap-1.5 rounded px-1.5 py-0.5" style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}>
          <span className="size-1.5 rounded-full" style={{ background: cam.is_online ? 'var(--color-success)' : 'var(--color-destructive)' }} />
          <span className="font-mono text-[10px] font-medium text-white">{cam.cam_id}</span>
        </div>
        {cam.motion_active && (
          <span className="rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider"
                style={{ background: 'oklch(0.78 0.15 75 / 0.2)', color: 'var(--color-warning)', boxShadow: '0 0 0 1px oklch(0.78 0.15 75 / 0.3)' }}>
            MOTION
          </span>
        )}
      </div>

      <div className="absolute inset-x-0 bottom-0 z-20 p-2 pointer-events-none" style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.7), transparent)' }}>
        <div className="truncate text-[11px] font-medium text-white">{cam.cam_ip}</div>
      </div>
    </button>
  )
}

// ── Grid tile ──────────────────────────────────────────────
function GridTileStream({ cam, onSelect }: { cam: Camera; onSelect: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null)

  const { data: streamInfo } = useQuery({
    queryKey: ['hls-url', cam.cam_id],
    queryFn:  () => fetchHlsUrl(cam.cam_id),
    enabled:  cam.is_online,
    staleTime: 45 * 60 * 1000,
    refetchInterval: 45 * 60 * 1000,
  })

  const toggleFullscreen = async () => {
    if (!document.fullscreenElement) {
      await containerRef.current?.requestFullscreen().catch(() => {})
    } else {
      await document.exitFullscreen().catch(() => {})
    }
  }

  return (
    <div ref={containerRef} className="relative overflow-hidden rounded-xl bg-black text-left group transition-all"
         style={{ aspectRatio: '16/9', boxShadow: '0 0 0 1px var(--color-border)' }}
         onMouseOver={e => (e.currentTarget.style.boxShadow = '0 0 0 1.5px oklch(0.78 0.14 200 / 0.5)')}
         onMouseOut={e => (e.currentTarget.style.boxShadow = '0 0 0 1px var(--color-border)')}>
      
      <button onClick={onSelect} className="absolute inset-0 z-10 w-full h-full cursor-pointer outline-none" />
      
      <HLSPlayer src={streamInfo?.hls_url ?? ''} camId={cam.cam_id} isOnline={cam.is_online} className="absolute inset-0" muted={true} autoPlay={true} />

      {/* Hover bar */}
      <div className="absolute inset-x-0 bottom-0 z-20 flex items-center justify-between px-3 py-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"
           style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.8), transparent)' }}>
        <div>
          <p className="font-mono text-xs text-white">{cam.cam_id}</p>
          {cam.cam_name && <p className="text-[10px]" style={{ color: 'var(--color-muted-foreground)' }}>{cam.cam_name}</p>}
        </div>
        <div className="flex items-center gap-3 pointer-events-auto">
          <span className="size-1.5 rounded-full" style={{ background: cam.is_online ? 'var(--color-success)' : 'var(--color-destructive)' }} />
          <button onClick={toggleFullscreen} className="text-white/70 hover:text-white transition-colors p-1">
            <Maximize2 size={14} />
          </button>
        </div>
      </div>
      
      {/* Top badges */}
      <div className="absolute inset-x-0 top-0 z-20 flex items-center justify-end p-2 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        {cam.motion_active && (
          <span className="rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider"
                style={{ background: 'oklch(0.78 0.15 75 / 0.2)', color: 'var(--color-warning)', boxShadow: '0 0 0 1px oklch(0.78 0.15 75 / 0.3)' }}>
            MOTION
          </span>
        )}
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────
export default function LiveView() {
  const [grid, setGrid]         = useState<GridN>(4)
  const [expanded, setExpanded] = useState<string | null>(null)

  const { data: cameras = [], refetch, isFetching } = useQuery({
    queryKey:       ['cameras'],
    queryFn:        fetchCameras,
    refetchInterval: 20_000,
  })

  const active  = cameras.filter(c => c.is_active)
  const online  = active.filter(c => c.is_online).length
  const offline = active.length - online
  const shown   = expanded ? active.filter(c => c.cam_id === expanded) : active.slice(0, grid * grid)
  const selectedCam = expanded ? active.find(c => c.cam_id === expanded) : active[0]
  const others  = active.filter(c => c.cam_id !== selectedCam?.cam_id).slice(0, 6)

  const cols: Record<GridN, string> = {
    1: 'grid-cols-1',
    2: 'grid-cols-2 lg:grid-cols-2',
    4: 'grid-cols-2 md:grid-cols-3 xl:grid-cols-4',
  }

  return (
    <div className="flex flex-col h-full p-4 lg:p-6 gap-5 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            Live Monitor
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
            {online} of {active.length} cameras online
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 rounded-lg p-1" style={{ background: 'var(--color-panel)', boxShadow: '0 0 0 1px var(--color-border)' }}>
            {([1, 2, 4] as GridN[]).map(n => (
              <button
                key={n}
                onClick={() => { setGrid(n); setExpanded(null) }}
                className="px-2.5 py-1 rounded-md font-mono text-xs font-semibold transition-colors"
                style={{
                  background: grid === n ? 'oklch(0.78 0.14 200 / 0.15)' : 'transparent',
                  color: grid === n ? 'var(--color-primary)' : 'var(--color-muted-foreground)',
                }}
              >
                {n === 1 ? '1×1' : n === 2 ? '2×2' : '4×4'}
              </button>
            ))}
          </div>
          {expanded && (
            <button onClick={() => setExpanded(null)} className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
                    style={{ color: 'var(--color-muted-foreground)', background: 'var(--color-secondary)' }}>
              Show all
            </button>
          )}
          <button onClick={() => refetch()} className="p-2 rounded-lg transition-colors bg-secondary hover:bg-secondary/80"
                  style={{ color: 'var(--color-muted-foreground)', background: 'var(--color-secondary)' }}>
            <RefreshCw size={14} className={isFetching ? 'animate-spin' : ''} style={{ color: isFetching ? 'var(--color-primary)' : undefined }} />
          </button>
        </div>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4 shrink-0">
        <KpiCard label="Live cameras" value={String(active.length)} sub={`${online} online`} tone="success" />
        <KpiCard label="Online" value={String(online)} sub="streaming" tone="success" />
        <KpiCard label="Offline" value={String(offline)} sub={offline > 0 ? 'needs attention' : 'all clear'} tone={offline > 0 ? 'warning' : 'muted'} />
        <KpiCard label="Total cameras" value={String(cameras.length)} sub="in registry" tone="muted" />
      </div>

      {/* Content */}
      {active.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <LayoutGrid size={36} style={{ color: 'var(--color-dim)' }} />
          <p className="text-sm" style={{ color: 'var(--color-foreground)' }}>No cameras registered</p>
          <p className="text-xs" style={{ color: 'var(--color-muted-foreground)' }}>Add cameras in the Cameras tab</p>
        </div>
      ) : !expanded ? (
        <div className={`grid ${cols[grid]} gap-3 flex-1 overflow-y-auto min-h-0 pb-4`}>
          {shown.map(cam => <GridTileStream key={cam.cam_id} cam={cam} onSelect={() => setExpanded(cam.cam_id)} />)}
        </div>
      ) : selectedCam ? (
        <div className="flex flex-col gap-5 xl:flex-row flex-1 min-h-0 overflow-y-auto pb-4 xl:overflow-hidden xl:pb-0">
          <div className="flex min-w-0 flex-[2.5] flex-col h-full">
            <FeaturedFeed cam={selectedCam} onCollapse={() => setExpanded(null)} />
          </div>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-2 xl:flex-1 xl:auto-rows-max xl:overflow-y-auto content-start">
            {others.map(cam => (
              <MiniTile key={cam.cam_id} cam={cam} selected={cam.cam_id === selectedCam.cam_id} onSelect={() => setExpanded(cam.cam_id)} />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
