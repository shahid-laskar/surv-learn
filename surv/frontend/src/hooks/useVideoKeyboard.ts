import { useEffect } from 'react'
import { nextPlaybackSpeed, stepVideoFrame } from '../lib/videoPlayback'

interface UseVideoKeyboardProps {
  containerRef: React.RefObject<HTMLDivElement | null>
  videoRef: React.RefObject<HTMLVideoElement | null>
  enabled?: boolean
  onSnapshot?: () => void
  onToggleFullscreen?: () => void
  onTogglePip?: () => void
  onPlaybackRateChange?: (rate: number) => void
  onFrameStep?: (forward: boolean) => void
}

export function useVideoKeyboard({
  containerRef,
  videoRef,
  enabled = true,
  onSnapshot,
  onToggleFullscreen,
  onTogglePip,
  onPlaybackRateChange,
  onFrameStep,
}: UseVideoKeyboardProps) {
  useEffect(() => {
    if (!enabled) return

    const isPlayerActive = () => {
      const el = containerRef.current
      if (!el) return false
      return el.matches(':hover') || el.contains(document.activeElement)
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA' ||
        document.activeElement?.tagName === 'SELECT'
      ) {
        return
      }

      if (!isPlayerActive()) return

      const video = videoRef.current
      if (!video) return

      switch (e.key.toLowerCase()) {
        case ' ':
          e.preventDefault()
          if (video.paused) {
            void video.play()
          } else {
            video.pause()
          }
          break
        case 'm':
          e.preventDefault()
          video.muted = !video.muted
          break
        case 'f':
          e.preventDefault()
          onToggleFullscreen?.()
          break
        case 'p':
          e.preventDefault()
          onTogglePip?.()
          break
        case 'arrowleft':
          e.preventDefault()
          video.currentTime = Math.max(0, video.currentTime - 5)
          break
        case 'arrowright':
          e.preventDefault()
          if (Number.isFinite(video.duration)) {
            video.currentTime = Math.min(video.duration - 0.05, video.currentTime + 5)
          }
          break
        case ',':
          e.preventDefault()
          if (onFrameStep) onFrameStep(false)
          else stepVideoFrame(video, false)
          break
        case '.':
          e.preventDefault()
          if (onFrameStep) onFrameStep(true)
          else stepVideoFrame(video, true)
          break
        case 's':
          e.preventDefault()
          onSnapshot?.()
          break
        case '+':
        case '=':
          e.preventDefault()
          {
            const rate = nextPlaybackSpeed(video.playbackRate, true)
            video.playbackRate = rate
            video.defaultPlaybackRate = rate
            onPlaybackRateChange?.(rate)
          }
          break
        case '-':
          e.preventDefault()
          {
            const rate = nextPlaybackSpeed(video.playbackRate, false)
            video.playbackRate = rate
            video.defaultPlaybackRate = rate
            onPlaybackRateChange?.(rate)
          }
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [containerRef, videoRef, enabled, onSnapshot, onToggleFullscreen, onTogglePip, onPlaybackRateChange, onFrameStep])
}
