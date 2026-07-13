import { useState, useCallback, useRef, useEffect } from 'react'

interface Point {
  x: number
  y: number
}

interface UseVideoZoomProps {
  containerRef: React.RefObject<HTMLDivElement | null>
  maxZoom?: number
}

export function useVideoZoom({ containerRef, maxZoom = 8 }: UseVideoZoomProps) {
  const [zoomLevel, setZoomLevel] = useState(1)
  const [panOffset, setPanOffset] = useState<Point>({ x: 0, y: 0 })
  const isDragging = useRef(false)
  const dragStart = useRef<Point>({ x: 0, y: 0 })

  const handleWheel = useCallback(
    (e: WheelEvent) => {
      if (!containerRef.current) return
      e.preventDefault()

      setZoomLevel((prevZoom) => {
        const delta = e.deltaY > 0 ? -0.5 : 0.5
        const newZoom = Math.min(Math.max(1, prevZoom + delta), maxZoom)

        if (newZoom === 1) {
          setPanOffset({ x: 0, y: 0 })
        } else if (newZoom !== prevZoom) {
          // Calculate pan offset to zoom into the cursor position
          const rect = containerRef.current!.getBoundingClientRect()
          const mouseX = e.clientX - rect.left
          const mouseY = e.clientY - rect.top

          setPanOffset((prevPan) => {
            const ratio = newZoom / prevZoom
            return {
              x: mouseX - (mouseX - prevPan.x) * ratio,
              y: mouseY - (mouseY - prevPan.y) * ratio,
            }
          })
        }

        return newZoom
      })
    },
    [containerRef, maxZoom]
  )

  const handleMouseDown = useCallback((e: MouseEvent) => {
    if (e.button !== 0 || zoomLevel <= 1) return
    e.preventDefault()
    isDragging.current = true
    dragStart.current = { x: e.clientX, y: e.clientY }
    if (containerRef.current) containerRef.current.style.cursor = 'grabbing'
  }, [zoomLevel, containerRef])

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging.current || zoomLevel === 1) return

      setPanOffset((prev) => ({
        x: prev.x + (e.clientX - dragStart.current.x),
        y: prev.y + (e.clientY - dragStart.current.y),
      }))
      dragStart.current = { x: e.clientX, y: e.clientY }
    },
    [zoomLevel]
  )

  const handleMouseUp = useCallback(() => {
    isDragging.current = false
    if (containerRef.current) {
      containerRef.current.style.cursor = zoomLevel > 1 ? 'grab' : 'default'
    }
  }, [containerRef, zoomLevel])

  const handleDoubleClick = useCallback(() => {
    setZoomLevel(1)
    setPanOffset({ x: 0, y: 0 })
  }, [])

  useEffect(() => {
    const element = containerRef.current
    if (!element) return

    element.addEventListener('wheel', handleWheel, { passive: false })
    element.addEventListener('mousedown', handleMouseDown)
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
    element.addEventListener('dblclick', handleDoubleClick)

    return () => {
      element.removeEventListener('wheel', handleWheel)
      element.removeEventListener('mousedown', handleMouseDown)
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
      element.removeEventListener('dblclick', handleDoubleClick)
    }
  }, [
    containerRef,
    handleWheel,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleDoubleClick,
  ])

  return { zoomLevel, panOffset, setZoomLevel, setPanOffset }
}
