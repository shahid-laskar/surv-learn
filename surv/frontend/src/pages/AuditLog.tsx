import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ClipboardList, Lock, RefreshCw, Filter } from 'lucide-react'
import { fetchAuditLogs, type AuditLog } from '../api/client'
import { hasPermission, hasRole } from '../lib/auth'

const ACTION_COLORS: Record<string, string> = {
  LOGIN:           'bg-green-500/10 text-green-300',
  LOGOUT:          'bg-dim/20 text-muted',
  CAMERA_CREATE:   'bg-blue-500/10 text-blue-300',
  CAMERA_UPDATE:   'bg-yellow-500/10 text-yellow-300',
  CAMERA_DELETE:   'bg-red-500/10 text-red-300',
}
function actionColor(action: string) {
  return ACTION_COLORS[action] ?? 'bg-dim/10 text-muted'
}

const ENTITY_TYPES = ['camera', 'user', 'customer', 'organization', 'role']
const ACTIONS = ['LOGIN', 'LOGOUT', 'CAMERA_CREATE', 'CAMERA_UPDATE', 'CAMERA_DELETE']

export default function AuditLog() {
  const [entityType, setEntityType] = useState('')
  const [action,     setAction]     = useState('')
  const [limit,      setLimit]      = useState(100)
  const [offset,     setOffset]     = useState(0)

  const canView = hasPermission('system.audit') || hasRole('SUPER_ADMIN')

  const { data: logs = [], isFetching, refetch } = useQuery({
    queryKey: ['audit', entityType, action, limit, offset],
    queryFn:  () => fetchAuditLogs({
      entity_type: entityType || undefined,
      action:      action || undefined,
      limit,
      offset,
    }),
    enabled: canView,
    refetchInterval: 30_000,
  })

  if (!canView) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 h-full">
        <Lock size={32} className="text-dim" />
        <p className="text-sm text-slate-300">system.audit permission required</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full p-4 gap-4 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold text-slate-100">Audit Log</h1>
          <p className="text-xs text-muted mt-0.5">
            {logs.length} events{isFetching && ' · refreshing...'}
          </p>
        </div>
        <button onClick={() => refetch()}
          className="p-1.5 text-muted hover:text-slate-200 rounded hover:bg-border transition-colors">
          <RefreshCw size={13} className={isFetching ? 'animate-spin text-accent' : ''} />
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 shrink-0">
        <Filter size={13} className="text-muted" />
        <select value={entityType} onChange={e => { setEntityType(e.target.value); setOffset(0) }}
          className="bg-surface border border-border rounded px-3 py-1.5 text-sm text-slate-200
                     focus:outline-none focus:border-accent/60 w-40">
          <option value="">All entities</option>
          {ENTITY_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={action} onChange={e => { setAction(e.target.value); setOffset(0) }}
          className="bg-surface border border-border rounded px-3 py-1.5 text-sm text-slate-200
                     focus:outline-none focus:border-accent/60 w-44">
          <option value="">All actions</option>
          {ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="flex-1 bg-panel border border-border rounded overflow-hidden flex flex-col min-h-0">
        {logs.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <ClipboardList size={32} className="text-dim" />
            <p className="text-sm text-slate-300">No audit logs found</p>
            <p className="text-xs text-muted">Adjust the filters or wait for activity</p>
          </div>
        ) : (
          <>
            <div className="overflow-y-auto flex-1">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-panel border-b border-border z-10">
                  <tr className="text-muted font-mono">
                    {['Time', 'User', 'Action', 'Entity', 'Entity ID', 'IP'].map(h => (
                      <th key={h} className="px-4 py-2.5 text-left">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log: AuditLog) => (
                    <tr key={log.id}
                      className="border-b border-border/50 hover:bg-border/20 transition-colors">
                      <td className="px-4 py-2.5 font-mono text-muted whitespace-nowrap">
                        {format(new Date(log.created_at), 'dd MMM HH:mm:ss')}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-slate-300">
                        {log.username ?? <span className="text-dim italic">system</span>}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className={`font-mono text-[10px] px-2 py-0.5 rounded ${actionColor(log.action)}`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-muted">{log.entity_type ?? '—'}</td>
                      <td className="px-4 py-2.5 font-mono text-muted">{log.entity_id ?? '—'}</td>
                      <td className="px-4 py-2.5 font-mono text-dim">{log.ip_address ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {logs.length >= limit && (
              <div className="border-t border-border px-4 py-2 flex justify-center shrink-0">
                <button onClick={() => setLimit(l => l + 100)}
                  className="px-3 py-1.5 text-muted hover:text-slate-200 text-xs font-medium rounded hover:bg-border transition-colors">
                  Load more
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
