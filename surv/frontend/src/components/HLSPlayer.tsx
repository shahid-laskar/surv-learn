import { useEffect, useRef, useState, forwardRef, useImperativeHandle, useCallback } from 'react'
import Hls from 'hls.js'
import { WifiOff, Loader } from 'lucide-react'
import VideoControls from './VideoControls'
import { useVideoZoom } from '../hooks/useVideoZoom'
import { useVideoKeyboard } from '../hooks/useVideoKeyboard'
import { applyPlaybackRate, stepVideoFrame } from '../lib/videoPlayback'

interface Props {
  src:            string
  camId:          string
  isOnline:       boolean
  className?:     string
  muted?:         boolean
  autoPlay?:      boolean
  onNeedsRefresh?: () => void
  showControls?:  boolean
  isLive?:        boolean
  forceNative?:   boolean
  onEnded?:       () => void
  playbackRate?:  number
  onPlaybackRateChange?: (rate: number) => void
}

export interface HLSPlayerRef {
  video: HTMLVideoElement | null
  snapshot: () => void
  setPlaybackRate: (rate: number) => void
  setZoom: (level: number) => void
  stepFrame: (forward: boolean) => void
  togglePip: () => void
  getStreamUrl: () => string
}

const HLSPlayer = forwardRef<HLSPlayerRef, Props>(({
  src,
  camId,
  isOnline,
  className = '',
  muted     = true,
  autoPlay  = true,
  onNeedsRefresh,
  showControls = false,
  isLive = false,
  forceNative = false,
  onEnded,
  playbackRate = 1,
  onPlaybackRateChange,
}, ref) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const hlsRef   = useRef<Hls | null>(null)
  const refreshRef = useRef(onNeedsRefresh)
  const onEndedRef = useRef(onEnded)
  const playbackRateRef = useRef(playbackRate)
  const suppressEndedRef = useRef(false)
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [state, setState] = useState<'loading' | 'playing' | 'error'>('loading')
  const [errorHint, setErrorHint] = useState('')
  const [latency, setLatency] = useState<number | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showOSD, setShowOSD] = useState(true)
  const [now, setNow] = useState(new Date())
  const [controlsVisible, setControlsVisible] = useState(false)

  const [levels, setLevels] = useState<{ height: number; bitrate: number }[]>([])
  const [currentLevel, setCurrentLevel] = useState<number>(-1)

  const { zoomLevel, panOffset, setZoomLevel, setPanOffset } = useVideoZoom({ containerRef })

  const revealControls = useCallback(() => {
    setControlsVisible(true)
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current)
    hideTimerRef.current = setTimeout(() => setControlsVisible(false), 3000)
  }, [])

  useEffect(() => {
    if (!showOSD) return
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [showOSD])

  useEffect(() => () => {
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current)
  }, [])

  const handleSnapshot = useCallback(() => {
    const video = videoRef.current
    if (!video || video.videoWidth === 0) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    canvas.toBlob(blob => {
      if (!blob) return
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `snapshot-${camId}-${new Date().toISOString().replace(/[:.]/g, '-')}.png`
      a.click()
      URL.revokeObjectURL(url)
    }, 'image/png')
  }, [camId])

  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return
    if (!document.fullscreenElement) {
      void containerRef.current.requestFullscreen()
    } else {
      void document.exitFullscreen()
    }
  }, [])

  const togglePip = useCallback(() => {
    const video = videoRef.current
    if (!video) return
    if (document.pictureInPictureElement) {
      void document.exitPictureInPicture()
    } else if (video.requestPictureInPicture) {
      void video.requestPictureInPicture()
    }
  }, [])

  const handleStepFrame = useCallback((forward: boolean) => {
    const video = videoRef.current
    if (!video) return
    stepVideoFrame(video, forward, {
      onStepping: stepping => { suppressEndedRef.current = stepping },
    })
  }, [])

  const handlePlaybackRateChange = useCallback((rate: number) => {
    playbackRateRef.current = rate
    const video = videoRef.current
    if (video) applyPlaybackRate(video, rate)
    onPlaybackRateChange?.(rate)
  }, [onPlaybackRateChange])

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  useVideoKeyboard({
    containerRef,
    videoRef,
    enabled: showControls,
    onSnapshot: handleSnapshot,
    onToggleFullscreen: toggleFullscreen,
    onTogglePip: togglePip,
    onPlaybackRateChange: handlePlaybackRateChange,
    onFrameStep: handleStepFrame,
  })

  useImperativeHandle(ref, () => ({
    get video() { return videoRef.current },
    snapshot: handleSnapshot,
    setPlaybackRate: (rate: number) => {
      if (videoRef.current) videoRef.current.playbackRate = rate
    },
    setZoom: (level: number) => {
      setZoomLevel(level)
    },
    stepFrame: handleStepFrame,
    togglePip,
    getStreamUrl: () => src,
  }), [handleSnapshot, setZoomLevel, togglePip, src, handleStepFrame])

  useEffect(() => { refreshRef.current = onNeedsRefresh }, [onNeedsRefresh])
  useEffect(() => { onEndedRef.current = onEnded }, [onEnded])
  useEffect(() => { playbackRateRef.current = playbackRate }, [playbackRate])

  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    applyPlaybackRate(video, playbackRate)
  }, [playbackRate])

  useEffect(() => {
    const video = videoRef.current
    if (!video || !isOnline || !src) {
      setState('loading')
      return
    }

    setState('loading')
    setErrorHint('')
    setLevels([])
    setCurrentLevel(-1)
    setLatency(null)

    const destroy = () => {
      hlsRef.current?.destroy()
      hlsRef.current = null
    }

    const resetVideo = () => {
      video.pause()
      video.removeAttribute('src')
      video.load()
    }

    const path = src.split('?')[0].toLowerCase()
    const applyRate = () => applyPlaybackRate(video, playbackRateRef.current)

    if (forceNative || path.endsWith('.mp4') || path.endsWith('.webm')) {
      video.src = src
      const onReady = () => {
        applyRate()
        setState('playing')
      }
      video.addEventListener('loadedmetadata', onReady, { once: true })
      if (video.readyState >= 1) onReady()

      const onError = () => {
        setErrorHint('Format not supported')
        setState('error')
      }
      video.addEventListener('error', onError, { once: true })
      if (autoPlay) void video.play().catch(() => {})
    } else if (Hls.isSupported()) {
      const hls = new Hls({
        lowLatencyMode: true,
        liveSyncDurationCount: 1,
        liveMaxLatencyDurationCount: 3,
        maxLiveSyncPlaybackRate: 1.5,
        backBufferLength: 30,
      })
      hlsRef.current = hls
      hls.loadSource(src)
      hls.attachMedia(video)
      hls.on(Hls.Events.MANIFEST_PARSED, (_event, data) => {
        setLevels(data.levels.map(l => ({ height: l.height, bitrate: l.bitrate })))
        setCurrentLevel(hls.currentLevel)
        applyRate()
        setState('playing')
        if (autoPlay) void video.play().catch(() => {})
      })

      hls.on(Hls.Events.LEVEL_SWITCHED, (_event, data) => {
        setCurrentLevel(data.level)
      })

      hls.on(Hls.Events.FRAG_CHANGED, () => {
        if (isLive && hls.latency > 0) {
          setLatency(hls.latency * 1000)
        }
      })
      hls.on(Hls.Events.ERROR, (_, d) => {
        if (!d.fatal) return

        const httpCode = d.response?.code
        if (httpCode === 401 || httpCode === 403) {
          setErrorHint('Session expired')
          refreshRef.current?.()
          return
        }

        if (d.type === Hls.ErrorTypes.NETWORK_ERROR) {
          hls.startLoad()
          return
        }

        if (d.type === Hls.ErrorTypes.MEDIA_ERROR) {
          setErrorHint('Codec not supported — use H.264 on camera')
          hls.recoverMediaError()
          return
        }

        setErrorHint('Stream unavailable')
        setState('error')
      })
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = src
      video.addEventListener('loadedmetadata', () => {
        applyRate()
        setState('playing')
      }, { once: true })
      video.addEventListener('error', () => {
        setErrorHint('Codec not supported — use H.264 on camera')
        setState('error')
      }, { once: true })
      if (autoPlay) void video.play().catch(() => {})
    } else {
      setErrorHint('HLS not supported')
      setState('error')
    }

    const endedHandler = () => {
      if (suppressEndedRef.current) return
      onEndedRef.current?.()
    }
    video.addEventListener('ended', endedHandler)

    return () => {
      destroy()
      video.removeEventListener('ended', endedHandler)
      resetVideo()
    }
  }, [src, isOnline, autoPlay, isLive, forceNative])

  const controlsShown = showControls && controlsVisible

  return (
    <div
      ref={containerRef}
      tabIndex={showControls ? 0 : -1}
      className={`relative w-full h-full bg-surface overflow-hidden group outline-none ${className}`}
      onMouseEnter={showControls ? revealControls : undefined}
      onMouseMove={showControls ? revealControls : undefined}
      onMouseLeave={showControls ? () => {
        if (hideTimerRef.current) clearTimeout(hideTimerRef.current)
        hideTimerRef.current = setTimeout(() => setControlsVisible(false), 800)
      } : undefined}
      onFocus={showControls ? revealControls : undefined}
    >
      {!isOnline && (
        <div className="scanlines absolute inset-0 bg-surface flex flex-col items-center justify-center gap-2 z-10">
          <WifiOff size={20} style={{ color: 'var(--color-dim)' }} />
          <span className="font-mono text-xs" style={{ color: 'var(--color-muted-foreground)' }}>NO SIGNAL</span>
          <span className="font-mono text-[10px] opacity-50" style={{ color: 'var(--color-muted-foreground)' }}>{camId}</span>
        </div>
      )}

      {isOnline && state === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <Loader size={18} className="animate-spin" style={{ color: 'var(--color-primary)' }} />
        </div>
      )}

      {isOnline && state === 'error' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-1.5 z-10 px-3 text-center">
          <WifiOff size={18} style={{ color: 'var(--color-destructive)' }} />
          <span className="font-mono text-xs" style={{ color: 'var(--color-destructive)' }}>STREAM ERROR</span>
          {errorHint && <span className="font-mono text-[10px]" style={{ color: 'var(--color-muted-foreground)' }}>{errorHint}</span>}
        </div>
      )}

      <div className="absolute inset-0 w-full h-full" style={{ overflow: 'hidden' }}>
        <video
          ref={videoRef}
          muted={muted}
          autoPlay={autoPlay}
          playsInline
          className={`w-full h-full object-cover transition-opacity duration-300
                      ${(!isOnline || state !== 'playing') ? 'opacity-0' : 'opacity-100'}`}
          style={{
            transform: `scale(${zoomLevel}) translate(${panOffset.x / zoomLevel}px, ${panOffset.y / zoomLevel}px)`,
            transformOrigin: 'center center',
            cursor: zoomLevel > 1 ? 'grab' : 'default',
          }}
        />
      </div>

      {showOSD && isLive && state === 'playing' && (
        <div className="absolute top-4 right-4 z-40 px-2 py-1 bg-black/60 backdrop-blur text-white font-mono text-sm rounded shadow-lg pointer-events-none">
          {now.toLocaleString()}
        </div>
      )}

      {showControls && isOnline && state === 'playing' && (
        <div
          className={`transition-opacity duration-300 ${controlsShown ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
          onMouseEnter={revealControls}
        >
          <VideoControls
            videoRef={videoRef}
            isLive={isLive}
            onSnapshot={handleSnapshot}
            onToggleFullscreen={toggleFullscreen}
            isFullscreen={isFullscreen}
            onTogglePip={togglePip}
            zoomLevel={zoomLevel}
            onZoomIn={() => setZoomLevel(z => Math.min(8, z + 0.5))}
            onZoomOut={() => setZoomLevel(z => Math.max(1, z - 0.5))}
            onResetZoom={() => { setZoomLevel(1); setPanOffset({ x: 0, y: 0 }) }}
            latency={latency}
            onToggleOSD={() => setShowOSD(prev => !prev)}
            levels={levels}
            currentLevel={currentLevel}
            onSetLevel={(level) => {
              if (hlsRef.current) hlsRef.current.currentLevel = level
            }}
            playbackRate={playbackRate}
            onPlaybackRateChange={handlePlaybackRateChange}
            onStepFrame={handleStepFrame}
          />
        </div>
      )}
    </div>
  )
})

HLSPlayer.displayName = 'HLSPlayer'

export default HLSPlayer
