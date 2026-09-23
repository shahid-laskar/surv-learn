/**
 * pages/AnprManagement.tsx
 * ANPR Management Plane, Fuzzy Trigram Plate Search, Hotlist Registry & Real-time Alerts.
 * Decoupled from inference hardware; provides operator audit trails and human corrections.
 */

import { useState } from 'react'
import {
  ShieldAlert, Search, PlusCircle, Edit3,
  RefreshCw, Car, AlertTriangle
} from 'lucide-react'
import { usePolling } from '../hooks/usePolling'
import {
  fetchAnprTransactions,
  searchAnprPlates,
  correctAnprPlate,
  fetchWatchlists,
  createWatchlistEntry,
  fetchWatchlistAlerts,
  acknowledgeWatchlistAlert,
  type AnprTransaction,
  type WatchlistEntry,
  type WatchlistAlert,
} from '../api/client'
import { useI18n } from '../lib/i18n'

export default function AnprManagement() {
  const { t } = useI18n()

  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<AnprTransaction[] | null>(null)
  const [searching, setSearching] = useState(false)

  // Correction state
  const [correctingTx, setCorrectingTx] = useState<AnprTransaction | null>(null)
  const [correctedPlateInput, setCorrectedPlateInput] = useState('')
  const [correctionNotes, setCorrectionNotes] = useState('')
  const [correctionLoading, setCorrectionLoading] = useState(false)

  // Watchlist add state
  const [showAddWlModal, setShowAddWlModal] = useState(false)
  const [wlPlate, setWlPlate] = useState('')
  const [wlCategory, setWlCategory] = useState('WANTED')
  const [wlSeverity, setWlSeverity] = useState('HIGH')
  const [wlReason, setWlReason] = useState('')
  const [wlCaseNo, setWlCaseNo] = useState('')
  const [wlLoading, setWlLoading] = useState(false)

  // Polling data
  const { data: recentReads = [], refetch: refetchReads } = usePolling<AnprTransaction[]>(
    ['anpr-transactions'], () => fetchAnprTransactions({ limit: 30 }), 10_000
  )
  const { data: watchlists = [], refetch: refetchWatchlists } = usePolling<WatchlistEntry[]>(
    ['anpr-watchlists'], () => fetchWatchlists(), 20_000
  )
  const { data: alerts = [], refetch: refetchAlerts } = usePolling<WatchlistAlert[]>(
    ['anpr-alerts-page'], () => fetchWatchlistAlerts(), 8_000
  )

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) {
      setSearchResults(null)
      return
    }
    setSearching(true)
    try {
      const results = await searchAnprPlates(searchQuery.trim(), 0.3)
      setSearchResults(results)
    } catch (err) {
      console.error('Fuzzy plate search failed:', err)
    } finally {
      setSearching(false)
    }
  }

  const handleCorrectSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!correctingTx || !correctedPlateInput.trim()) return

    setCorrectionLoading(true)
    try {
      await correctAnprPlate(correctingTx.id, correctedPlateInput.trim().toUpperCase(), correctionNotes)
      setCorrectingTx(null)
      setCorrectedPlateInput('')
      setCorrectionNotes('')
      refetchReads()
      refetchAlerts()
    } catch (err) {
      console.error('Failed to correct plate:', err)
    } finally {
      setCorrectionLoading(false)
    }
  }

  const handleCreateWatchlist = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!wlPlate.trim() || !wlReason.trim()) return

    setWlLoading(true)
    try {
      await createWatchlistEntry({
        plate_number: wlPlate.trim().toUpperCase(),
        category: wlCategory,
        severity: wlSeverity,
        reason: wlReason.trim(),
        case_number: wlCaseNo.trim() || undefined,
        reporting_authority: 'Kerala Police Pathanamthitta',
      })
      setShowAddWlModal(false)
      setWlPlate('')
      setWlReason('')
      setWlCaseNo('')
      refetchWatchlists()
    } catch (err) {
      console.error('Failed to register watchlist vehicle:', err)
    } finally {
      setWlLoading(false)
    }
  }

  const handleAcknowledge = async (id: number) => {
    try {
      await acknowledgeWatchlistAlert(id, 'Verified and acknowledged by control operator')
      refetchAlerts()
    } catch (err) {
      console.error('Failed to acknowledge alert:', err)
    }
  }

  const displayedReads = searchResults !== null ? searchResults : recentReads

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4"
           style={{ borderColor: 'var(--color-border)' }}>
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="text-rose-400" size={22} />
            <h1 className="text-xl font-bold tracking-tight text-white">
              {t('anpr_title')}
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {t('anpr_subtitle')}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddWlModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-500 text-white transition shadow"
          >
            <PlusCircle size={14} />
            {t('anpr_add_watchlist')}
          </button>
          <button
            onClick={() => { refetchReads(); refetchWatchlists(); refetchAlerts(); }}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            <RefreshCw size={13} />
            {t('refresh')}
          </button>
        </div>
      </div>

      {/* ── Real-Time Active Interceptions Banner ────────────────────────── */}
      {alerts.some(a => a.status === 'ACTIVE') && (
        <div className="p-4 rounded-xl border border-rose-800/80 bg-rose-950/30 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-300 flex items-center gap-1.5">
              <AlertTriangle size={15} className="animate-bounce" />
              Active Police Hotlist Interceptions ({alerts.filter(a => a.status === 'ACTIVE').length})
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
            {alerts.filter(a => a.status === 'ACTIVE').map(a => (
              <div key={a.id} className="p-3 rounded-lg border border-rose-800/60 bg-rose-900/40 flex items-center justify-between">
                <div>
                  <div className="font-mono text-sm font-black text-rose-200">{a.plate_number}</div>
                  <div className="text-[11px] text-rose-300">Severity: <b>{a.severity}</b> · Cam #{a.camera_id || 'N/A'}</div>
                </div>
                <button
                  onClick={() => handleAcknowledge(a.id)}
                  className="px-2.5 py-1 text-xs font-bold rounded bg-rose-500 hover:bg-rose-400 text-white transition"
                >
                  {t('anpr_ack_btn')}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Search Bar (Fuzzy Trigram) ───────────────────────────────────── */}
      <div className="p-4 rounded-xl border bg-slate-900/80 border-slate-800">
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
            <input
              type="text"
              placeholder={t('anpr_search_placeholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white font-mono uppercase focus:outline-none focus:border-sky-500"
            />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="px-4 py-2 text-xs font-bold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition disabled:opacity-50 flex items-center gap-1.5"
          >
            <Search size={14} />
            {searching ? 'Searching...' : t('submit')}
          </button>
          {searchResults !== null && (
            <button
              type="button"
              onClick={() => { setSearchResults(null); setSearchQuery(''); }}
              className="px-3 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
            >
              Reset
            </button>
          )}
        </form>
      </div>

      {/* ── Two-Column Layout: Detections & Watchlist Grid ────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: ANPR Detections Feed */}
        <div className="lg:col-span-2 p-5 rounded-xl border bg-slate-900/80 border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Car size={16} className="text-sky-400" />
              {searchResults !== null ? `Search Results (${searchResults.length})` : t('anpr_live_reads')}
            </h2>
            <span className="text-xs text-slate-400">
              Contract Decoupled Ingest Plane
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 text-slate-400 font-medium">
                <tr>
                  <th className="py-2.5 px-3">Plate Read</th>
                  <th className="py-2.5 px-3">Vehicle</th>
                  <th className="py-2.5 px-3">{t('anpr_confidence')}</th>
                  <th className="py-2.5 px-3">Camera</th>
                  <th className="py-2.5 px-3">Captured At</th>
                  <th className="py-2.5 px-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {displayedReads.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-6 text-slate-500 font-sans">
                      No ANPR vehicle records found.
                    </td>
                  </tr>
                ) : (
                  displayedReads.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3">
                        <div className="font-bold text-white tracking-wide">{tx.plate_number}</div>
                        {tx.is_corrected && (
                          <div className="text-[10px] text-amber-400 font-sans">
                            Corrected from: {tx.original_plate}
                          </div>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-sky-400 font-sans">
                        {tx.vehicle_type || 'CAR'} {tx.vehicle_color ? `(${tx.vehicle_color})` : ''}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`font-semibold ${tx.confidence >= 0.85 ? 'text-emerald-400' : 'text-amber-400'}`}>
                          {(tx.confidence * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-sans text-slate-400">
                        #{tx.camera_id || 'N/A'}
                      </td>
                      <td className="py-2.5 px-3 font-sans text-slate-400 text-[11px]">
                        {new Date(tx.captured_at).toLocaleTimeString()}
                      </td>
                      <td className="py-2.5 px-3">
                        <button
                          onClick={() => {
                            setCorrectingTx(tx)
                            setCorrectedPlateInput(tx.plate_number)
                          }}
                          className="px-2 py-1 text-[11px] font-sans font-semibold rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1 transition"
                        >
                          <Edit3 size={11} />
                          {t('anpr_correct_btn')}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Col: Registered Police Watchlist Vehicles */}
        <div className="p-5 rounded-xl border bg-slate-900/80 border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <ShieldAlert size={16} className="text-rose-400" />
              {t('anpr_watchlist_title')} ({watchlists.length})
            </h2>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {watchlists.length === 0 ? (
              <div className="text-center py-6 text-xs text-slate-500">
                No hotlist vehicles currently enrolled.
              </div>
            ) : (
              watchlists.map((wl) => (
                <div
                  key={wl.id}
                  className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-bold text-white tracking-wide">
                      {wl.plate_number}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      wl.severity === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                      wl.severity === 'HIGH' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                      'bg-slate-800 text-slate-300'
                    }`}>
                      {wl.category}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300">
                    {wl.reason}
                  </div>
                  {wl.case_number && (
                    <div className="text-[11px] text-slate-500 font-mono">
                      Ref: {wl.case_number}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* ── Modal: Operator Plate Correction ─────────────────────────────── */}
      {correctingTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Edit3 size={18} className="text-sky-400" />
              Manual Plate Read Correction
            </h3>
            <p className="text-xs text-slate-400">
              Audit trail will record your correction, preserve original OCR read, and re-check police hotlists.
            </p>

            <form onSubmit={handleCorrectSubmit} className="space-y-3 pt-2">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Original OCR Read
                </label>
                <input
                  type="text"
                  value={correctingTx.plate_number}
                  disabled
                  className="w-full px-3 py-2 text-sm rounded-lg bg-slate-950 border border-slate-800 text-slate-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Corrected License Plate *
                </label>
                <input
                  type="text"
                  value={correctedPlateInput}
                  onChange={(e) => setCorrectedPlateInput(e.target.value)}
                  required
                  className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white font-mono uppercase focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Reason / Operator Notes
                </label>
                <input
                  type="text"
                  placeholder="e.g. Corrected 0 to O based on high-res snapshot"
                  value={correctionNotes}
                  onChange={(e) => setCorrectionNotes(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setCorrectingTx(null)}
                  className="flex-1 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                >
                  {t('cancel')}
                </button>
                <button
                  type="submit"
                  disabled={correctionLoading}
                  className="flex-1 py-2 text-xs font-bold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition disabled:opacity-50"
                >
                  {correctionLoading ? 'Saving...' : t('submit')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal: Add Vehicle to Watchlist ──────────────────────────────── */}
      {showAddWlModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <PlusCircle size={18} className="text-rose-400" />
              Enroll Hotlist / Watchlist Vehicle
            </h3>
            <p className="text-xs text-slate-400">
              Immediate alert interception will trigger upon any camera plate match.
            </p>

            <form onSubmit={handleCreateWatchlist} className="space-y-3 pt-2">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Vehicle Number *
                </label>
                <input
                  type="text"
                  placeholder="e.g. KL07BH9999"
                  value={wlPlate}
                  onChange={(e) => setWlPlate(e.target.value)}
                  required
                  className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white font-mono uppercase focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">
                    Category
                  </label>
                  <select
                    value={wlCategory}
                    onChange={(e) => setWlCategory(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-rose-500"
                  >
                    <option value="WANTED">WANTED</option>
                    <option value="STOLEN">STOLEN</option>
                    <option value="SUSPICIOUS">SUSPICIOUS</option>
                    <option value="VIP">VIP</option>
                    <option value="CUSTOM">CUSTOM</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">
                    Severity
                  </label>
                  <select
                    value={wlSeverity}
                    onChange={(e) => setWlSeverity(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-rose-500"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Reason / Police Alert Notes *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Vehicle wanted in Pathanamthitta theft case"
                  value={wlReason}
                  onChange={(e) => setWlReason(e.target.value)}
                  required
                  className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-rose-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Case Number / FIR Ref (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. FIR-112/2026/PTA"
                  value={wlCaseNo}
                  onChange={(e) => setWlCaseNo(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg bg-slate-800 border border-slate-700 text-white font-mono focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddWlModal(false)}
                  className="flex-1 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                >
                  {t('cancel')}
                </button>
                <button
                  type="submit"
                  disabled={wlLoading}
                  className="flex-1 py-2 text-xs font-bold rounded-lg bg-rose-600 hover:bg-rose-500 text-white transition disabled:opacity-50"
                >
                  {wlLoading ? 'Registering...' : t('submit')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
