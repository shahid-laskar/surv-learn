import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ClipboardList, Lock, RefreshCw, Filter } from 'lucide-react'
import { fetchAuditLogs, type AuditLog } from '../api/client'
import { hasPermission, hasRole } from '../lib/auth'

const ACTION_TONE: Record<string, { bg: string; color: string }> = {
  LOGIN:         { bg: 'oklch(0.72 0.17 150 / 0.1)', color: 'var(--color-success)' },
  LOGOUT:        { bg: 'oklch(0.32 0.025 260 / 0.2)', color: 'var(--color-muted-foreground)' },
  CAMERA_CREATE: { bg: 'oklch(0.78 0.14 200 / 0.1)', color: 'var(--color-primary)' },
  CAMERA_UPDATE: { bg: 'oklch(0.78 0.15 75 / 0.1)',  color: 'var(--color-warning)' },
  CAMERA_DELETE: { bg: 'oklch(0.62 0.22 25 / 0.1)',  color: 'var(--color-destructive)' },
}
function actionTone(action: string) {
  return ACTION_TONE[action] ?? { bg: 'oklch(0.32 0.025 260 / 0.1)', color: 'var(--color-muted-foreground)' }
}

const ENTITY_TYPES = ['camera', 'user', 'customer', 'organization', 'role']
const ACTIONS = ['LOGIN', 'LOGOUT', 'CAMERA_CREATE', 'CAMERA_UPDATE', 'CAMERA_DELETE']

const selectStyle = {
  background: 'oklch(0.28 0.03 260 / 0.5)',
  color: 'var(--color-foreground)',
  boxShadow: '0 0 0 1px var(--color-border)',
} as React.CSSProperties

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
        <Lock size={32} style={{ color: 'var(--color-dim)' }} />
        <p className="text-sm" style={{ color: 'var(--color-foreground)' }}>system.audit permission required</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full p-4 lg:p-6 gap-5 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold flex items-center gap-2"
              style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            <ClipboardList size={16} style={{ color: 'var(--color-primary)' }} />
            Audit Log
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
            {logs.length} events{isFetching && ' · refreshing...'}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 rounded-lg transition-colors"
          style={{ color: 'var(--color-muted-foreground)' }}>
          <RefreshCw size={13} className={isFetching ? 'animate-spin' : ''}
                     style={{ color: isFetching ? 'var(--color-primary)' : undefined }} />
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl p-3 shrink-0"
           style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
        <Filter size={14} className="ml-1" style={{ color: 'var(--color-muted-foreground)' }} />
        <select value={entityType} onChange={e => { setEntityType(e.target.value); setOffset(0) }}
          className="rounded-md px-2 py-1 text-xs outline-none" style={selectStyle}>
          <option value="">All entities</option>
          {ENTITY_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={action} onChange={e => { setAction(e.target.value); setOffset(0) }}
          className="rounded-md px-2 py-1 text-xs outline-none" style={selectStyle}>
          <option value="">All actions</option>
          {ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="flex-1 rounded-2xl overflow-hidden flex flex-col min-h-0"
           style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
        {logs.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <ClipboardList size={32} style={{ color: 'var(--color-dim)' }} />
            <p className="text-sm" style={{ color: 'var(--color-foreground)' }}>No audit logs found</p>
            <p className="text-xs" style={{ color: 'var(--color-muted-foreground)' }}>Adjust the filters or wait for activity</p>
          </div>
        ) : (
          <>
            <div className="overflow-y-auto flex-1">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="text-[11px] font-medium uppercase tracking-widest sticky top-0"
                      style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)', background: 'oklch(0.22 0.035 260)' }}>
                    {['Time', 'User', 'Action', 'Entity', 'Entity ID', 'IP'].map(h => (
                      <th key={h} className="px-4 py-3 text-left">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log: AuditLog) => {
                    const tone = actionTone(log.action)
                    return (
                      <tr key={log.id} className="transition-colors last:border-b-0"
                          style={{ borderBottom: '1px solid var(--color-border)' }}
                          onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)')}
                          onMouseOut={e => (e.currentTarget.style.background = 'transparent')}>
                        <td className="px-4 py-2.5 font-mono whitespace-nowrap"
                            style={{ color: 'var(--color-muted-foreground)' }}>
                          {format(new Date(log.created_at), 'dd MMM HH:mm:ss')}
                        </td>
                        <td className="px-4 py-2.5 font-mono"
                            style={{ color: 'var(--color-foreground)' }}>
                          {log.username ?? <span style={{ color: 'var(--color-dim)', fontStyle: 'italic' }}>system</span>}
                        </td>
                        <td className="px-4 py-2.5">
                          <span className="font-mono text-[10px] px-2 py-0.5 rounded-md"
                                style={{ background: tone.bg, color: tone.color }}>
                            {log.action}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-xs capitalize"
                            style={{ color: 'var(--color-muted-foreground)' }}>{log.entity_type ?? '—'}</td>
                        <td className="px-4 py-2.5 font-mono text-xs"
                            style={{ color: 'var(--color-muted-foreground)' }}>{log.entity_id ?? '—'}</td>
                        <td className="px-4 py-2.5 font-mono text-xs"
                            style={{ color: 'var(--color-dim)' }}>{log.ip_address ?? '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            {logs.length >= limit && (
              <div className="px-4 py-2 flex justify-center shrink-0"
                   style={{ borderTop: '1px solid var(--color-border)' }}>
                <button onClick={() => setLimit(l => l + 100)}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
                  style={{ color: 'var(--color-muted-foreground)', background: 'var(--color-secondary)' }}>
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
