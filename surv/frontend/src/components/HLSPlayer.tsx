import { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'
import { WifiOff, Loader } from 'lucide-react'

interface Props {
  src:       string
  camId:     string
  isOnline:  boolean
  className?: string
  muted?:    boolean
  autoPlay?: boolean
}

type State = 'loading' | 'playing' | 'error'

export default function HLSPlayer({
  src,
  camId,
  isOnline,
  className = '',
  muted     = true,
  autoPlay  = true,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const hlsRef   = useRef<Hls | null>(null)
  const [state, setState] = useState<State>('loading')

  useEffect(() => {
    const video = videoRef.current
    if (!video || !isOnline) { setState('loading'); return }

    setState('loading')

    const destroy = () => {
      hlsRef.current?.destroy()
      hlsRef.current = null
    }

    if (Hls.isSupported()) {
      const hls = new Hls({ lowLatencyMode: true, liveSyncDurationCount: 2 })
      hlsRef.current = hls
      hls.loadSource(src)
      hls.attachMedia(video)
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => {})
        setState('playing')
      })
      hls.on(Hls.Events.ERROR, (_, d) => { if (d.fatal) setState('error') })
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = src
      video.addEventListener('loadedmetadata', () => setState('playing'), { once: true })
      video.addEventListener('error',          () => setState('error'),   { once: true })
      if (autoPlay) video.play().catch(() => {})
    } else {
      setState('error')
    }

    return destroy
  }, [src, isOnline, autoPlay])

  return (
    <div className={`relative w-full h-full bg-surface overflow-hidden ${className}`}>

      {/* Offline — scanline effect */}
      {!isOnline && (
        <div className="scanlines absolute inset-0 bg-surface flex flex-col items-center justify-center gap-2 z-10">
          <WifiOff size={20} className="text-dim" />
          <span className="font-mono text-xs text-muted">NO SIGNAL</span>
          <span className="font-mono text-[10px] text-muted/50">{camId}</span>
        </div>
      )}

      {/* Loading */}
      {isOnline && state === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <Loader size={18} className="text-accent animate-spin" />
        </div>
      )}

      {/* Stream error */}
      {isOnline && state === 'error' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-1.5 z-10">
          <WifiOff size={18} className="text-alert" />
          <span className="font-mono text-xs text-alert">STREAM ERROR</span>
        </div>
      )}

      {/* LIVE badge */}
      {isOnline && state === 'playing' && (
        <div className="absolute top-2 left-2 z-20 flex items-center gap-1.5
                        bg-surface/70 backdrop-blur-sm rounded px-1.5 py-0.5">
          <span className="size-1.5 rounded-full bg-online animate-[pulse-dot_2s_ease-in-out_infinite]" />
          <span className="font-mono text-[9px] text-online tracking-widest">LIVE</span>
        </div>
      )}

      {/* Camera ID */}
      <div className="absolute bottom-2 right-2 z-20">
        <span className="font-mono text-[9px] text-muted/70 bg-surface/60
                         backdrop-blur-sm rounded px-1.5 py-0.5">
          {camId}
        </span>
      </div>

      <video
        ref={videoRef}
        muted={muted}
        autoPlay={autoPlay}
        playsInline
        className={`w-full h-full object-cover transition-opacity duration-300
                    ${(!isOnline || state !== 'playing') ? 'opacity-0' : 'opacity-100'}`}
      />
    </div>
  )
}
