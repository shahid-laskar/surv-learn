import React, { useState, useEffect } from 'react'
import {
  Play, Pause, Volume2, VolumeX, Maximize, Minimize,
  PictureInPicture, Camera as CameraIcon, Settings,
  SkipBack, SkipForward, ZoomIn, ZoomOut
} from 'lucide-react'
import { PLAYBACK_SPEEDS, stepVideoFrame } from '../lib/videoPlayback'

interface QualityLevel {
  height: number
  bitrate: number
}

interface VideoControlsProps {
  videoRef: React.RefObject<HTMLVideoElement | null>
  isLive?: boolean
  onSnapshot?: () => void
  onToggleFullscreen?: () => void
  isFullscreen?: boolean
  onTogglePip?: () => void
  zoomLevel?: number
  onZoomIn?: () => void
  onZoomOut?: () => void
  onResetZoom?: () => void
  latency?: number | null
  onToggleOSD?: () => void
  levels?: QualityLevel[]
  currentLevel?: number
  onSetLevel?: (level: number) => void
  playbackRate?: number
  onPlaybackRateChange?: (rate: number) => void
  onStepFrame?: (forward: boolean) => void
}

export default function VideoControls({
  videoRef,
  isLive = false,
  onSnapshot,
  onToggleFullscreen,
  isFullscreen = false,
  onTogglePip,
  zoomLevel = 1,
  onZoomIn,
  onZoomOut,
  onResetZoom,
  latency = null,
  onToggleOSD,
  levels = [],
  currentLevel = -1,
  onSetLevel,
  playbackRate: controlledRate,
  onPlaybackRateChange,
  onStepFrame,
}: VideoControlsProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(true)
  const [volume, setVolume] = useState(1)
  const [showVolume, setShowVolume] = useState(false)
  const [internalRate, setInternalRate] = useState(1)
  const playbackRate = controlledRate ?? internalRate
  const [showSettings, setShowSettings] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)
    const handleVolumeChange = () => {
      setIsMuted(video.muted || video.volume === 0)
      setVolume(video.volume)
    }
    const handleRateChange = () => {
      const rate = video.playbackRate
      if (controlledRate == null) setInternalRate(rate)
      onPlaybackRateChange?.(rate)
    }
    const handleTimeUpdate = () => setProgress(video.currentTime)
    const handleDurationChange = () => setDuration(video.duration)

    video.addEventListener('play', handlePlay)
    video.addEventListener('pause', handlePause)
    video.addEventListener('volumechange', handleVolumeChange)
    video.addEventListener('ratechange', handleRateChange)
    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('durationchange', handleDurationChange)
    video.addEventListener('loadedmetadata', handleDurationChange)

    setIsPlaying(!video.paused)
    setIsMuted(video.muted || video.volume === 0)
    setVolume(video.volume)
    if (controlledRate == null) setInternalRate(video.playbackRate)
    else if (video.playbackRate !== controlledRate) video.playbackRate = controlledRate
    setProgress(video.currentTime)
    setDuration(video.duration || 0)

    return () => {
      video.removeEventListener('play', handlePlay)
      video.removeEventListener('pause', handlePause)
      video.removeEventListener('volumechange', handleVolumeChange)
      video.removeEventListener('ratechange', handleRateChange)
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('durationchange', handleDurationChange)
      video.removeEventListener('loadedmetadata', handleDurationChange)
    }
  }, [videoRef, controlledRate, onPlaybackRateChange])

  const setRate = (rate: number) => {
    const video = videoRef.current
    if (!video) return
    video.playbackRate = rate
    video.defaultPlaybackRate = rate
    if (controlledRate == null) setInternalRate(rate)
    onPlaybackRateChange?.(rate)
    setShowSettings(false)
  }

  const stepFrame = (forward: boolean) => {
    if (onStepFrame) {
      onStepFrame(forward)
      return
    }
    const video = videoRef.current
    if (!video) return
    stepVideoFrame(video, forward)
  }

  const togglePlay = () => {
    const video = videoRef.current
    if (!video) return
    if (video.paused) {
      void video.play()
    } else {
      video.pause()
    }
  }

  const toggleMute = () => {
    const video = videoRef.current
    if (!video) return
    video.muted = !video.muted
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current
    if (!video) return
    const newVolume = parseFloat(e.target.value)
    video.volume = newVolume
    if (newVolume > 0 && video.muted) {
      video.muted = false
    }
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const video = videoRef.current
    if (!video) return
    const newTime = parseFloat(e.target.value)
    video.currentTime = newTime
    setProgress(newTime)
  }

  const formatTime = (seconds: number) => {
    if (!Number.isFinite(seconds)) return '0:00'
    const m = Math.floor(seconds / 60)
    const s = Math.floor(seconds % 60)
    return `${m}:${s < 10 ? '0' : ''}${s}`
  }

  const formatLatency = (ms: number | null) => {
    if (ms === null) return '--'
    return `${(ms / 1000).toFixed(1)}s`
  }

  const formatQuality = (level: QualityLevel) => {
    if (level.height > 0) return `${level.height}p`
    if (level.bitrate > 0) return `${Math.round(level.bitrate / 1000)}k`
    return 'Unknown'
  }

  const hasQualities = levels.length > 1

  return (
    <div
      className="absolute inset-x-0 bottom-0 z-10 flex flex-col justify-end p-4 pointer-events-none"
      style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 100%)' }}
      onClick={e => e.stopPropagation()}
    >
      {!isLive && duration > 0 && Number.isFinite(duration) && (
        <div className="w-full flex items-center gap-3 pointer-events-auto mb-2 text-xs font-mono text-white/80">
          <span>{formatTime(progress)}</span>
          <input
            type="range"
            min="0"
            max={duration}
            step="0.1"
            value={Math.min(progress, duration)}
            onChange={handleSeek}
            className="flex-1 accent-primary h-1.5 bg-white/30 rounded-full appearance-none cursor-pointer"
            aria-label="Seek"
          />
          <span>{formatTime(duration)}</span>
        </div>
      )}

      <div className="flex items-center justify-between pointer-events-auto">
        <div className="flex items-center gap-4">
          <button
            onClick={togglePlay}
            className="text-white hover:text-primary transition-colors"
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause size={20} fill="currentColor" /> : <Play size={20} fill="currentColor" />}
          </button>

          <div
            className="flex items-center gap-2 group relative"
            onMouseEnter={() => setShowVolume(true)}
            onMouseLeave={() => setShowVolume(false)}
          >
            <button
              onClick={toggleMute}
              className="text-white hover:text-primary transition-colors"
              aria-label={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
            </button>
            <div className={`overflow-hidden transition-all duration-300 ease-in-out ${showVolume ? 'w-24 opacity-100' : 'w-0 opacity-0'}`}>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                className="w-full accent-primary h-1 bg-white/30 rounded-full appearance-none cursor-pointer"
                aria-label="Volume"
              />
            </div>
          </div>

          {isLive && (
            <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-black/40 text-xs font-mono">
              <span className="size-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-white">
                LIVE
                {latency !== null && (
                  <span className="text-white/60 ml-1">{formatLatency(latency)}</span>
                )}
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-4">
          {!isLive && (
            <div className="flex items-center gap-1 text-white">
              <button
                onClick={() => stepFrame(false)}
                title="Step Backward (,)"
                aria-label="Step backward one frame"
                className="hover:text-primary transition-colors p-1"
              >
                <SkipBack size={16} />
              </button>
              <button
                onClick={() => stepFrame(true)}
                title="Step Forward (.)"
                aria-label="Step forward one frame"
                className="hover:text-primary transition-colors p-1"
              >
                <SkipForward size={16} />
              </button>
            </div>
          )}

          <div className="flex items-center gap-1 text-white bg-black/40 rounded px-1">
            <button
              onClick={onZoomOut}
              disabled={zoomLevel <= 1}
              className="hover:text-primary disabled:opacity-30 transition-colors p-1"
              title="Zoom Out"
              aria-label="Zoom out"
            >
              <ZoomOut size={16} />
            </button>
            <span
              className="text-xs font-mono w-8 text-center cursor-pointer hover:text-primary"
              onClick={onResetZoom}
              title="Reset Zoom"
            >
              {zoomLevel.toFixed(1)}x
            </span>
            <button
              onClick={onZoomIn}
              disabled={zoomLevel >= 8}
              className="hover:text-primary disabled:opacity-30 transition-colors p-1"
              title="Zoom In"
              aria-label="Zoom in"
            >
              <ZoomIn size={16} />
            </button>
          </div>

          <button
            onClick={onSnapshot}
            className="text-white hover:text-primary transition-colors"
            title="Snapshot (s)"
            aria-label="Take snapshot"
          >
            <CameraIcon size={18} />
          </button>

          <div className="relative">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={`text-white hover:text-primary transition-colors ${playbackRate !== 1 || (hasQualities && currentLevel !== -1) ? 'text-primary' : ''}`}
              title="Settings / Speed / Quality"
              aria-label="Settings"
              aria-expanded={showSettings}
            >
              <Settings size={18} />
            </button>

            {showSettings && (
              <div className="absolute bottom-full right-0 mb-2 w-36 bg-zinc-900/95 border border-white/10 rounded-lg shadow-xl overflow-hidden backdrop-blur-sm max-h-64 overflow-y-auto">
                <div className="px-3 py-2 text-xs font-semibold text-white/50 border-b border-white/10">Speed</div>
                {PLAYBACK_SPEEDS.map(rate => (
                  <button
                    key={rate}
                    onClick={() => setRate(rate)}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-white/10 transition-colors ${playbackRate === rate ? 'text-primary bg-primary/10' : 'text-white'}`}
                  >
                    {rate === 1 ? 'Normal' : `${rate}×`}
                  </button>
                ))}

                {hasQualities && onSetLevel && (
                  <>
                    <div className="px-3 py-2 text-xs font-semibold text-white/50 border-b border-t border-white/10">Quality</div>
                    <button
                      onClick={() => { onSetLevel(-1); setShowSettings(false) }}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-white/10 transition-colors ${currentLevel === -1 ? 'text-primary bg-primary/10' : 'text-white'}`}
                    >
                      Auto
                    </button>
                    {levels.map((level, idx) => (
                      <button
                        key={idx}
                        onClick={() => { onSetLevel(idx); setShowSettings(false) }}
                        className={`w-full text-left px-3 py-2 text-sm hover:bg-white/10 transition-colors ${currentLevel === idx ? 'text-primary bg-primary/10' : 'text-white'}`}
                      >
                        {formatQuality(level)}
                      </button>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>

          {onToggleOSD && (
            <button
              onClick={onToggleOSD}
              className="text-white hover:text-primary transition-colors text-xs font-bold border border-white/50 rounded px-1.5 py-0.5"
              title="Toggle Timestamp OSD"
              aria-label="Toggle timestamp overlay"
            >
              OSD
            </button>
          )}

          {onTogglePip && (
            <button
              onClick={onTogglePip}
              className="text-white hover:text-primary transition-colors"
              title="Picture in Picture (p)"
              aria-label="Picture in picture"
            >
              <PictureInPicture size={18} />
            </button>
          )}

          <button
            onClick={onToggleFullscreen}
            className="text-white hover:text-primary transition-colors"
            title="Fullscreen (f)"
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <Minimize size={18} /> : <Maximize size={18} />}
          </button>
        </div>
      </div>
    </div>
  )
}
