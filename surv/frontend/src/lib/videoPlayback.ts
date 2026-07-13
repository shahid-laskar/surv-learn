export const PLAYBACK_SPEEDS = [0.25, 0.5, 1, 1.5, 2, 4, 8, 16] as const

export type PlaybackSpeed = (typeof PLAYBACK_SPEEDS)[number]

const FRAME_STEP = 1 / 30
const END_EPSILON = 0.05

export function nextPlaybackSpeed(current: number, faster: boolean): PlaybackSpeed {
  const idx = PLAYBACK_SPEEDS.findIndex(s => s >= current - 0.01)
  const base = idx === -1 ? PLAYBACK_SPEEDS.length - 1 : idx
  const next = faster
    ? Math.min(base + 1, PLAYBACK_SPEEDS.length - 1)
    : Math.max(base - 1, 0)
  return PLAYBACK_SPEEDS[next]
}

export function clampPlaybackSpeed(rate: number): PlaybackSpeed {
  const match = PLAYBACK_SPEEDS.find(s => s === rate)
  if (match) return match
  const idx = PLAYBACK_SPEEDS.findIndex(s => s >= rate)
  return idx === -1 ? PLAYBACK_SPEEDS[PLAYBACK_SPEEDS.length - 1] : PLAYBACK_SPEEDS[idx]
}

export function stepVideoFrame(
  video: HTMLVideoElement,
  forward: boolean,
  opts?: { onStepping?: (stepping: boolean) => void },
) {
  if (video.readyState < HTMLMediaElement.HAVE_METADATA) return

  if (!video.paused) video.pause()

  const duration = video.duration
  let target = video.currentTime + (forward ? FRAME_STEP : -FRAME_STEP)

  if (Number.isFinite(duration) && duration > 0) {
    const safeEnd = Math.max(0, duration - END_EPSILON)
    target = Math.max(0, Math.min(safeEnd, target))
  } else {
    target = Math.max(0, target)
  }

  if (Math.abs(target - video.currentTime) < 0.0001) return

  opts?.onStepping?.(true)
  const onSeeked = () => {
    video.removeEventListener('seeked', onSeeked)
    opts?.onStepping?.(false)
  }
  video.addEventListener('seeked', onSeeked)
  video.currentTime = target
}

export function applyPlaybackRate(video: HTMLVideoElement, rate: number) {
  const clamped = clampPlaybackSpeed(rate)
  try {
    video.playbackRate = clamped
    video.defaultPlaybackRate = clamped
  } catch {
    video.playbackRate = 1
    video.defaultPlaybackRate = 1
  }
  return video.playbackRate
}
