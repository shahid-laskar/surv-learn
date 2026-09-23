/**
 * pages/IcccCommand.tsx
 * Integrated Command & Control Centre (ICCC) Dashboard & Common Operating Picture.
 * Composite single-pane-of-glass interface combining:
 * 1. GIS Map with real-time camera/parking statuses
 * 2. Video Wall / Priority Live Player
 * 3. Parking Grounds Live Occupancy
 * 4. ANPR Interception Alerts
 * 5. Edge & System Health indicators
 * Fully bilingual (English / Malayalam).
 */

import { useState } from 'react'
import {
  ShieldAlert, Video, Car, MapPin,
  RefreshCw, Radio
} from 'lucide-react'
import { usePolling } from '../hooks/usePolling'
import {
  fetchCameras,
  fetchParkingOccupancy,
  fetchWatchlistAlerts,
  acknowledgeWatchlistAlert,
  type Camera,
  type ParkingOccupancySummary,
  type WatchlistAlert,
} from '../api/client'
import GisMap from '../components/GisMap'
import HLSPlayer from '../components/HLSPlayer'
import { useI18n } from '../lib/i18n'

export default function IcccCommand() {
  const { t } = useI18n()
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null)
  const [ackingId, setAckingId] = useState<number | null>(null)

  // Live polling intervals for ICCC control room
  const { data: cameras = [], refetch: refetchCameras } = usePolling<Camera[]>(
    ['iccc-cameras'], fetchCameras, 15_000
  )
  const { data: occupancy, refetch: refetchOccupancy } = usePolling<ParkingOccupancySummary>(
    ['iccc-occupancy'], () => fetchParkingOccupancy(), 10_000
  )
  const { data: alerts = [], refetch: refetchAlerts } = usePolling<WatchlistAlert[]>(
    ['iccc-alerts'], () => fetchWatchlistAlerts({ status_filter: 'ACTIVE' }), 8_000
  )

  const activeCameras = cameras.filter(c => c.is_online)

  const handleAcknowledge = async (alertId: number) => {
    try {
      setAckingId(alertId)
      await acknowledgeWatchlistAlert(alertId, 'Acknowledged from ICCC Command Console')
      refetchAlerts()
    } catch (err) {
      console.error('Failed to acknowledge alert:', err)
    } finally {
      setAckingId(null)
    }
  }

  const currentStreamCam = selectedCamera || activeCameras[0] || null

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* ── Top Header & KPI Bar ─────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4"
           style={{ borderColor: 'var(--color-border)' }}>
        <div>
          <div className="flex items-center gap-2">
            <Radio className="text-emerald-500 animate-pulse" size={20} />
            <h1 className="text-xl font-bold tracking-tight text-white">
              {t('iccc_title')}
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {t('iccc_subtitle')}
          </p>
        </div>

        {/* Quick Refresh */}
        <button
          onClick={() => { refetchCameras(); refetchOccupancy(); refetchAlerts(); }}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          <RefreshCw size={13} />
          {t('refresh')}
        </button>
      </div>

      {/* ── KPI Metrics Ribbon ───────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Cameras */}
        <div className="p-4 rounded-xl border bg-slate-900/60 border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">{t('iccc_all_cameras')}</span>
            <Video size={16} className="text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {cameras.length}
            <span className="text-xs font-normal text-emerald-400 ml-2">
              ({activeCameras.length} {t('iccc_online_cameras')})
            </span>
          </div>
        </div>

        {/* Parking Occupancy */}
        <div className="p-4 rounded-xl border bg-slate-900/60 border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">{t('iccc_parking_occupancy')}</span>
            <Car size={16} className="text-sky-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {occupancy ? `${occupancy.total_occupied} / ${occupancy.total_capacity}` : '—'}
            <span className="text-xs font-normal text-sky-400 ml-2">
              ({occupancy?.overall_occupancy_pct ?? 0}%)
            </span>
          </div>
        </div>

        {/* Available Parking Slots */}
        <div className="p-4 rounded-xl border bg-slate-900/60 border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">{t('iccc_available_slots')}</span>
            <MapPin size={16} className="text-teal-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-teal-400">
            {occupancy ? occupancy.total_available : '—'}
          </div>
        </div>

        {/* Active ANPR Alerts */}
        <div className="p-4 rounded-xl border bg-slate-900/60 border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">{t('iccc_anpr_alerts')}</span>
            <ShieldAlert size={16} className="text-rose-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-400">
            {alerts.length}
            <span className="text-xs font-normal text-slate-400 ml-2">
              {t('status_active')}
            </span>
          </div>
        </div>
      </div>

      {/* ── Main Command Grid: GIS Map & Live Priority Feed ──────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Interactive GIS Map */}
        <div className="lg:col-span-2 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
              <MapPin size={15} className="text-sky-400" />
              {t('iccc_gis_map')}
            </h2>
            <span className="text-xs text-slate-400">
              Sabarimala / Nilakkal Sector Grid
            </span>
          </div>
          <GisMap
            cameras={cameras}
            parkingZones={occupancy?.zones || []}
            selectedCameraId={currentStreamCam?.id}
            onSelectCamera={(cam) => setSelectedCamera(cam)}
            height="520px"
          />
        </div>

        {/* Right Col: Video Wall Live Stream */}
        <div className="space-y-4">
          <div className="p-4 rounded-xl border bg-slate-900/70 border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
                <Video size={15} className="text-emerald-400" />
                {t('iccc_video_wall')}
              </h2>
              {currentStreamCam && (
                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                  {currentStreamCam.cam_id}
                </span>
              )}
            </div>

            {currentStreamCam ? (
              <div className="space-y-2">
                <div className="aspect-video w-full rounded-lg overflow-hidden border border-slate-800 bg-black">
                  <HLSPlayer
                    src={`/api/v1/streams/${currentStreamCam.cam_id}/index.m3u8`}
                    camId={currentStreamCam.cam_id}
                    isOnline={currentStreamCam.is_online}
                    showControls
                    autoPlay
                    muted
                  />
                </div>
                <div className="text-xs text-slate-300">
                  <b>{currentStreamCam.cam_name || currentStreamCam.cam_id}</b>
                  <div className="text-[11px] text-slate-500">
                    Location: Nilakkal Main Corridor · Protocol: {currentStreamCam.stream_protocol || 'rtsp'}
                  </div>
                </div>
              </div>
            ) : (
              <div className="aspect-video flex items-center justify-center text-xs text-slate-500 bg-slate-950 rounded-lg">
                No active camera feed selected
              </div>
            )}
          </div>

          {/* Real-time ANPR Interception Alerts Feed */}
          <div className="p-4 rounded-xl border bg-slate-900/70 border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
                <ShieldAlert size={15} className="text-rose-400" />
                {t('iccc_anpr_alerts')} ({alerts.length})
              </h2>
            </div>

            <div className="space-y-2 max-h-[190px] overflow-y-auto">
              {alerts.length === 0 ? (
                <div className="text-center py-4 text-xs text-slate-500">
                  No active watchlist alerts
                </div>
              ) : (
                alerts.map((al) => (
                  <div
                    key={al.id}
                    className="p-2.5 rounded-lg border border-rose-900/40 bg-rose-950/20 flex items-center justify-between gap-2"
                  >
                    <div>
                      <div className="font-mono text-xs font-bold text-rose-300">
                        🚨 {al.plate_number}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Severity: <span className="font-semibold text-rose-400">{al.severity}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleAcknowledge(al.id)}
                      disabled={ackingId === al.id}
                      className="px-2 py-1 text-[10px] font-semibold rounded bg-rose-600 hover:bg-rose-500 text-white transition disabled:opacity-50"
                    >
                      {ackingId === al.id ? '...' : t('anpr_ack_btn')}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Nilakkal Grounds Occupancy Overview ──────────────────────────── */}
      <div className="p-4 rounded-xl border bg-slate-900/60 border-slate-800 space-y-3">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
          <Car size={15} className="text-sky-400" />
          {t('iccc_parking_occupancy')}
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {occupancy?.zones.map((zone) => {
            const isFull = zone.available_slots === 0
            const isNearFull = zone.occupancy_pct >= 85
            const statusBg = isFull
              ? 'border-rose-800 bg-rose-950/20'
              : isNearFull
              ? 'border-amber-800 bg-amber-950/20'
              : 'border-slate-800 bg-slate-900/80'

            return (
              <div key={zone.id} className={`p-3 rounded-lg border ${statusBg}`}>
                <div className="flex items-center justify-between text-xs font-bold text-slate-200">
                  <span>{zone.zone_code}</span>
                  <span className="text-[10px] text-slate-400 font-mono">{zone.vehicle_type}</span>
                </div>
                <div className="mt-1 text-base font-extrabold text-white">
                  {zone.current_occupancy} / {zone.total_capacity}
                </div>
                <div className="mt-1 flex items-center justify-between text-[10px] text-slate-400">
                  <span>Avail: {zone.available_slots}</span>
                  <span className={isFull ? 'text-rose-400 font-bold' : ''}>
                    {zone.occupancy_pct}%
                  </span>
                </div>
                <div className="mt-2 h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${isFull ? 'bg-rose-500' : isNearFull ? 'bg-amber-500' : 'bg-sky-500'}`}
                    style={{ width: `${Math.min(100, zone.occupancy_pct)}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
