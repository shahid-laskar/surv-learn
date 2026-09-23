/**
 * pages/ParkingManagement.tsx
 * Sabarimala Nilakkal Parking Management System (PMS) Console.
 * Zone Allocation, Automated Barrier Trigger, POS Slip Generation & Exit Fee Processing.
 */

import React, { useState } from 'react'
import { Car, Printer, ArrowRightCircle, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react'
import { usePolling } from '../hooks/usePolling'
import {
  fetchParkingOccupancy,
  submitVehicleEntry,
  submitVehicleExit,
  type ParkingOccupancySummary,
  type ParkingSlipOut,
} from '../api/client'
import { useI18n } from '../lib/i18n'

export default function ParkingManagement() {
  const { t } = useI18n()

  // State for forms
  const [entryPlate, setEntryPlate] = useState('')
  const [entryVehicleType, setEntryVehicleType] = useState('LMV')
  const [entryPreferredZone, setEntryPreferredZone] = useState<number | ''>('')
  const [issuedSlip, setIssuedSlip] = useState<ParkingSlipOut | null>(null)
  const [entryError, setEntryError] = useState<string | null>(null)
  const [entryLoading, setEntryLoading] = useState(false)

  const [exitIdentifier, setExitIdentifier] = useState('')
  const [completedExitSlip, setCompletedExitSlip] = useState<ParkingSlipOut | null>(null)
  const [exitError, setExitError] = useState<string | null>(null)
  const [exitLoading, setExitLoading] = useState(false)

  const { data: occupancy, refetch } = usePolling<ParkingOccupancySummary>(
    ['parking-occupancy-page'], () => fetchParkingOccupancy(), 8_000
  )

  const handleEntry = async (e: React.FormEvent) => {
    e.preventDefault()
    setEntryError(null)
    setIssuedSlip(null)
    if (!entryPlate.trim()) return

    setEntryLoading(true)
    try {
      const slip = await submitVehicleEntry({
        vehicle_number: entryPlate.trim().toUpperCase(),
        vehicle_type: entryVehicleType,
        preferred_zone_id: entryPreferredZone === '' ? undefined : Number(entryPreferredZone),
      })
      setIssuedSlip(slip)
      setEntryPlate('')
      refetch()
    } catch (err: any) {
      setEntryError(err?.response?.data?.detail || 'Failed to allocate parking slot')
    } finally {
      setEntryLoading(false)
    }
  }

  const handleExit = async (e: React.FormEvent) => {
    e.preventDefault()
    setExitError(null)
    setCompletedExitSlip(null)
    if (!exitIdentifier.trim()) return

    setExitLoading(true)
    try {
      const isSlip = exitIdentifier.trim().startsWith('SLIP-')
      const slip = await submitVehicleExit({
        entry_slip_number: isSlip ? exitIdentifier.trim() : undefined,
        vehicle_number: !isSlip ? exitIdentifier.trim().toUpperCase() : undefined,
      })
      setCompletedExitSlip(slip)
      setExitIdentifier('')
      refetch()
    } catch (err: any) {
      setExitError(err?.response?.data?.detail || 'Failed to process vehicle exit')
    } finally {
      setExitLoading(false)
    }
  }

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4"
           style={{ borderColor: 'var(--color-border)' }}>
        <div>
          <div className="flex items-center gap-2">
            <Car className="text-sky-400" size={22} />
            <h1 className="text-xl font-bold tracking-tight text-white">
              {t('pms_title')}
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {t('pms_subtitle')}
          </p>
        </div>

        <button
          onClick={() => refetch()}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
        >
          <RefreshCw size={13} />
          {t('refresh')}
        </button>
      </div>

      {/* ── Top Roll-up Cards ────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border bg-slate-900/60 border-slate-800">
          <span className="text-xs font-medium text-slate-400">{t('iccc_total_slots')}</span>
          <div className="mt-2 text-2xl font-bold text-white">{occupancy?.total_capacity ?? 0}</div>
        </div>
        <div className="p-4 rounded-xl border bg-slate-900/60 border-slate-800">
          <span className="text-xs font-medium text-slate-400">{t('iccc_occupied_slots')}</span>
          <div className="mt-2 text-2xl font-bold text-sky-400">{occupancy?.total_occupied ?? 0}</div>
        </div>
        <div className="p-4 rounded-xl border bg-slate-900/60 border-slate-800">
          <span className="text-xs font-medium text-slate-400">{t('iccc_available_slots')}</span>
          <div className="mt-2 text-2xl font-bold text-teal-400">{occupancy?.total_available ?? 0}</div>
        </div>
        <div className="p-4 rounded-xl border bg-slate-900/60 border-slate-800">
          <span className="text-xs font-medium text-slate-400">Total Grounds</span>
          <div className="mt-2 text-2xl font-bold text-slate-200">{occupancy?.total_zones ?? 0}</div>
        </div>
      </div>

      {/* ── Operations Forms (Entry & Exit) ──────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Entry Allocation Form */}
        <div className="p-5 rounded-xl border bg-slate-900/80 border-slate-800 space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <ArrowRightCircle size={16} className="text-emerald-400" />
            {t('pms_new_entry')}
          </h2>

          <form onSubmit={handleEntry} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                {t('pms_plate')} *
              </label>
              <input
                type="text"
                placeholder="e.g. KL-01-AB-1234"
                value={entryPlate}
                onChange={(e) => setEntryPlate(e.target.value)}
                required
                className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white font-mono uppercase focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  {t('pms_type')}
                </label>
                <select
                  value={entryVehicleType}
                  onChange={(e) => setEntryVehicleType(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="LMV">LMV / Car</option>
                  <option value="BUS">KSRTC / Bus</option>
                  <option value="HMV">Heavy Motor Vehicle (HMV)</option>
                  <option value="2W">Two Wheeler (2W)</option>
                  <option value="3W">Three Wheeler (3W)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Preferred Ground (Optional)
                </label>
                <select
                  value={entryPreferredZone}
                  onChange={(e) => setEntryPreferredZone(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="">Auto Select (Recommended)</option>
                  {occupancy?.zones.map((z) => (
                    <option key={z.id} value={z.id} disabled={z.available_slots === 0}>
                      {z.zone_code} - {z.name} ({z.available_slots} free)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {entryError && (
              <div className="p-3 text-xs rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-2">
                <AlertCircle size={14} className="shrink-0" />
                {entryError}
              </div>
            )}

            <button
              type="submit"
              disabled={entryLoading}
              className="w-full py-2.5 px-4 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Printer size={15} />
              {entryLoading ? 'Allocating...' : t('pms_allocate_btn')}
            </button>
          </form>

          {/* Generated Thermal Slip Preview */}
          {issuedSlip && (
            <div className="p-4 rounded-lg border border-emerald-800/80 bg-emerald-950/20 space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-emerald-400">
                <span className="flex items-center gap-1.5">
                  <CheckCircle size={14} /> Official Parking Slip Issued
                </span>
                <span className="font-mono">{issuedSlip.slip_number}</span>
              </div>
              <div className="text-xs text-slate-300 font-mono space-y-0.5 pt-1">
                <div>Vehicle: <b>{issuedSlip.vehicle_number}</b> ({issuedSlip.vehicle_type})</div>
                <div>Allocated Ground: <b className="text-sky-300">{issuedSlip.zone_code} - {issuedSlip.zone_name}</b></div>
                <div>Entry Time: {new Date(issuedSlip.entry_time).toLocaleString()}</div>
                <div>Boom Barrier: <span className="text-emerald-400 font-bold">AUTOMATED OPEN</span></div>
              </div>
            </div>
          )}
        </div>

        {/* Exit Processing Form */}
        <div className="p-5 rounded-xl border bg-slate-900/80 border-slate-800 space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <ArrowRightCircle size={16} className="text-sky-400" />
            {t('pms_process_exit')}
          </h2>

          <form onSubmit={handleExit} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Entry Slip Number or Vehicle Plate *
              </label>
              <input
                type="text"
                placeholder="SLIP-2026... or KL01AB1234"
                value={exitIdentifier}
                onChange={(e) => setExitIdentifier(e.target.value)}
                required
                className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white font-mono uppercase focus:outline-none focus:border-sky-500"
              />
            </div>

            {exitError && (
              <div className="p-3 text-xs rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-2">
                <AlertCircle size={14} className="shrink-0" />
                {exitError}
              </div>
            )}

            <button
              type="submit"
              disabled={exitLoading}
              className="w-full py-2.5 px-4 text-xs font-bold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <CheckCircle size={15} />
              {exitLoading ? 'Calculating...' : t('pms_exit_btn')}
            </button>
          </form>

          {/* Completed Exit Receipt Preview */}
          {completedExitSlip && (
            <div className="p-4 rounded-lg border border-sky-800/80 bg-sky-950/20 space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-sky-400">
                <span className="flex items-center gap-1.5">
                  <CheckCircle size={14} /> Exit Settlement Complete
                </span>
                <span className="font-mono">{completedExitSlip.slip_number}</span>
              </div>
              <div className="text-xs text-slate-300 font-mono space-y-0.5 pt-1">
                <div>Vehicle: <b>{completedExitSlip.vehicle_number}</b></div>
                <div>Duration: <b>{completedExitSlip.duration_minutes ?? 0} minutes</b></div>
                <div>Total Fee Collected: <b className="text-emerald-400 text-sm">₹{completedExitSlip.fee_amount.toFixed(2)}</b></div>
                <div>Status: <span className="text-emerald-400 font-bold">{completedExitSlip.status}</span></div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Grounds Table ────────────────────────────────────────────────── */}
      <div className="p-5 rounded-xl border bg-slate-900/80 border-slate-800 space-y-4">
        <h2 className="text-sm font-semibold text-slate-200">
          Nilakkal Parking Grounds Status Grid (G01 - G12)
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="border-b border-slate-800 text-slate-400 font-medium">
              <tr>
                <th className="py-2.5 px-3">Ground Code</th>
                <th className="py-2.5 px-3">Name</th>
                <th className="py-2.5 px-3">Vehicle Class</th>
                <th className="py-2.5 px-3">Capacity</th>
                <th className="py-2.5 px-3">Occupancy</th>
                <th className="py-2.5 px-3">Available Slots</th>
                <th className="py-2.5 px-3">Occupancy %</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {occupancy?.zones.map((zone) => (
                <tr key={zone.id} className="hover:bg-slate-800/30">
                  <td className="py-2.5 px-3 font-bold text-white">{zone.zone_code}</td>
                  <td className="py-2.5 px-3 font-sans">{zone.name}</td>
                  <td className="py-2.5 px-3 text-sky-400">{zone.vehicle_type}</td>
                  <td className="py-2.5 px-3">{zone.total_capacity}</td>
                  <td className="py-2.5 px-3 text-white font-bold">{zone.current_occupancy}</td>
                  <td className="py-2.5 px-3 text-teal-400 font-bold">{zone.available_slots}</td>
                  <td className="py-2.5 px-3">
                    <span className={zone.occupancy_pct >= 90 ? 'text-rose-400 font-bold' : ''}>
                      {zone.occupancy_pct}%
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                      ACTIVE
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
