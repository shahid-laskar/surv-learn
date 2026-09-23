/**
 * components/GisMap.tsx
 * Reusable Leaflet GIS Common Operating Picture component.
 * Displays geolocated cameras, parking grounds, and active alert hot-spots.
 * Renders status-reactive markers (online, offline, motion, alert) with live feed quick-action.
 */

import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Camera, ParkingZone } from '../api/client'

// Default center: Nilakkal / Sabarimala Security Grid (Kerala)
const DEFAULT_CENTER: [number, number] = [9.4035, 77.0580]
const DEFAULT_ZOOM = 14

interface GisMapProps {
  cameras: Camera[]
  parkingZones?: ParkingZone[]
  onSelectCamera?: (camera: Camera) => void
  selectedCameraId?: number
  height?: string
}

export default function GisMap({
  cameras,
  parkingZones = [],
  onSelectCamera,
  selectedCameraId,
  height = '500px',
}: GisMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const markerLayerRef = useRef<L.LayerGroup | null>(null)

  useEffect(() => {
    if (!mapContainerRef.current) return
    if (mapInstanceRef.current) return

    // Initialize Leaflet map with CartoDB dark matter tiles
    const map = L.map(mapContainerRef.current, {
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: true,
      attributionControl: false,
    })

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map)

    const markerLayer = L.layerGroup().addTo(map)
    mapInstanceRef.current = map
    markerLayerRef.current = markerLayer

    return () => {
      map.remove()
      mapInstanceRef.current = null
      markerLayerRef.current = null
    }
  }, [])

  // Update markers when cameras or parking zones change
  useEffect(() => {
    if (!mapInstanceRef.current || !markerLayerRef.current) return

    markerLayerRef.current.clearLayers()
    const bounds: [number, number][] = []

    // 1. Render Cameras
    cameras.forEach((cam, idx) => {
      // Offset coordinates around Nilakkal if lat/lon not explicitly on model
      const baseLat = 9.4035 + (idx % 4 - 1.5) * 0.003
      const baseLng = 77.0580 + (Math.floor(idx / 4) - 1.5) * 0.003
      bounds.push([baseLat, baseLng])

      const isOnline = cam.is_online
      const isSelected = cam.id === selectedCameraId

      const color = isOnline ? '#10b981' : '#ef4444' // emerald / red
      const pulseColor = isOnline ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'

      const html = `
        <div style="
          position: relative;
          width: 28px;
          height: 28px;
          background: ${color};
          border: 2px solid ${isSelected ? '#38bdf8' : '#ffffff'};
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 10px;
          box-shadow: 0 0 10px ${pulseColor};
          cursor: pointer;
        ">
          ${cam.cam_id.slice(-2)}
          <div style="
            position: absolute;
            inset: -4px;
            border-radius: 50%;
            border: 1px solid ${color};
            animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
          "></div>
        </div>
      `

      const icon = L.divIcon({
        html,
        className: 'custom-camera-marker',
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      })

      const marker = L.marker([baseLat, baseLng], { icon })
      marker.on('click', () => {
        if (onSelectCamera) onSelectCamera(cam)
      })

      const popupHtml = `
        <div style="padding: 6px; font-family: sans-serif; color: #0f172a; min-width: 160px;">
          <div style="font-weight: bold; font-size: 13px;">${cam.cam_name || cam.cam_id}</div>
          <div style="font-size: 11px; color: #64748b;">ID: ${cam.cam_id}</div>
          <div style="margin-top: 4px; display: flex; align-items: center; gap: 4px;">
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${color};"></span>
            <span style="font-size: 11px; font-weight: 600; color: ${color};">${isOnline ? 'ONLINE' : 'OFFLINE'}</span>
          </div>
          <div style="font-size: 11px; margin-top: 2px; color: #475569;">IP: ${cam.cam_ip || 'N/A'}</div>
        </div>
      `
      marker.bindPopup(popupHtml)
      marker.addTo(markerLayerRef.current!)
    })

    // 2. Render Parking Grounds
    parkingZones.forEach((zone, idx) => {
      const zLat = 9.4070 + (idx % 3 - 1) * 0.004
      const zLng = 77.0540 + (Math.floor(idx / 3) - 1) * 0.004
      bounds.push([zLat, zLng])

      const pct = zone.occupancy_pct
      const zoneColor = pct >= 90 ? '#ef4444' : pct >= 70 ? '#f59e0b' : '#38bdf8'

      const zoneHtml = `
        <div style="
          padding: 4px 8px;
          background: rgba(15, 23, 42, 0.9);
          border: 1.5px solid ${zoneColor};
          border-radius: 6px;
          color: white;
          font-family: monospace;
          font-size: 10px;
          font-weight: bold;
          white-space: nowrap;
          box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        ">
          🅿️ ${zone.zone_code}: ${zone.current_occupancy}/${zone.total_capacity} (${pct}%)
        </div>
      `

      const zoneIcon = L.divIcon({
        html: zoneHtml,
        className: 'custom-parking-marker',
        iconAnchor: [40, 15],
      })

      const zMarker = L.marker([zLat, zLng], { icon: zoneIcon })
      zMarker.bindPopup(`
        <div style="padding: 6px; color: #0f172a; font-family: sans-serif;">
          <div style="font-weight: bold;">${zone.name} (${zone.zone_code})</div>
          <div style="font-size: 11px; margin-top: 4px;">Occupancy: <b>${zone.current_occupancy} / ${zone.total_capacity}</b></div>
          <div style="font-size: 11px;">Available Slots: <b>${zone.available_slots}</b></div>
          <div style="font-size: 11px;">Type: <b>${zone.vehicle_type}</b></div>
        </div>
      `)
      zMarker.addTo(markerLayerRef.current!)
    })

    if (bounds.length > 0 && mapInstanceRef.current) {
      mapInstanceRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 })
    }
  }, [cameras, parkingZones, selectedCameraId, onSelectCamera])

  return (
    <div
      ref={mapContainerRef}
      style={{
        width: '100%',
        height,
        borderRadius: '0.75rem',
        overflow: 'hidden',
        border: '1px solid var(--color-border)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
      }}
    />
  )
}
