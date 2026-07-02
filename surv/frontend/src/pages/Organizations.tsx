import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Building2, Plus, X, ChevronRight, ChevronDown, GitBranch } from 'lucide-react'
import {
  fetchOrgs, createOrg, fetchCircles, fetchBAs,
  type Organization, type OrganizationCreate, type OrgType,
} from '../api/client'
import { hasPermission, hasRole } from '../lib/auth'

const ORG_TYPES: OrgType[] = ['ROOT', 'CIRCLE', 'BA', 'SSA', 'DISTRICT', 'SITE', 'NOC']

const TYPE_COLORS: Record<OrgType, string> = {
  ROOT:     'bg-purple-500/20 text-purple-300 border-purple-500/30',
  CIRCLE:   'bg-blue-500/20 text-blue-300 border-blue-500/30',
  BA:       'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  SSA:      'bg-teal-500/20 text-teal-300 border-teal-500/30',
  DISTRICT: 'bg-green-500/20 text-green-300 border-green-500/30',
  SITE:     'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  NOC:      'bg-orange-500/20 text-orange-300 border-orange-500/30',
}

const EMPTY: OrganizationCreate = { code: '', name: '', type: 'CIRCLE' }

function buildTree(orgs: Organization[]): Map<number | null, Organization[]> {
  const map = new Map<number | null, Organization[]>()
  for (const org of orgs) {
    const key = org.parent_id ?? null
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(org)
  }
  return map
}

function OrgNode({
  org, tree, depth, expandedIds, onToggle,
}: {
  org: Organization
  tree: Map<number | null, Organization[]>
  depth: number
  expandedIds: Set<number>
  onToggle: (id: number) => void
}) {
  const children = tree.get(org.id) ?? []
  const hasChildren = children.length > 0
  const isExpanded = expandedIds.has(org.id)

  return (
    <>
      <tr className="border-b border-border/50 hover:bg-border/20 transition-colors">
        <td className="px-4 py-2.5">
          <div className="flex items-center gap-2" style={{ paddingLeft: `${depth * 20}px` }}>
            <button
              onClick={() => onToggle(org.id)}
              className={`size-5 flex items-center justify-center rounded transition-colors ${
                hasChildren ? 'text-muted hover:text-slate-300' : 'text-dim cursor-default'
              }`}
            >
              {hasChildren
                ? (isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />)
                : <span className="size-1.5 rounded-full bg-dim inline-block" />
              }
            </button>
            <GitBranch size={13} className="text-muted shrink-0" />
            <span className="font-mono text-xs text-slate-300">{org.code}</span>
          </div>
        </td>
        <td className="px-4 py-2.5 text-sm text-slate-200">{org.name}</td>
        <td className="px-4 py-2.5">
          <span className={`font-mono text-[10px] px-2 py-0.5 rounded border ${TYPE_COLORS[org.type as OrgType] ?? 'bg-dim/20 text-muted border-dim'}`}>
            {org.type}
          </span>
        </td>
        <td className="px-4 py-2.5">
          <span className={`size-1.5 rounded-full inline-block ${org.is_active ? 'bg-online' : 'bg-dim'}`} />
        </td>
      </tr>
      {isExpanded && children.map(child => (
        <OrgNode
          key={child.id}
          org={child}
          tree={tree}
          depth={depth + 1}
          expandedIds={expandedIds}
          onToggle={onToggle}
        />
      ))}
    </>
  )
}

export default function Organizations() {
  const qc = useQueryClient()
  const [showForm, setShowForm]       = useState(false)
  const [form, setForm]               = useState<OrganizationCreate>(EMPTY)
  const [error, setError]             = useState<string | null>(null)
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())

  const canEdit = hasPermission('system.settings') || hasRole('SUPER_ADMIN')

  const { data: orgs = [], isFetching } = useQuery({
    queryKey:        ['orgs'],
    queryFn:         fetchOrgs,
    refetchInterval: 30_000,
  })

  const { data: circles = [] } = useQuery({ queryKey: ['circles'], queryFn: fetchCircles })
  const { data: bas = [] }     = useQuery({
    queryKey: ['bas', form.circle_id],
    queryFn:  () => fetchBAs(form.circle_id),
    enabled:  !!form.circle_id,
  })

  const createMut = useMutation({
    mutationFn: createOrg,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['orgs'] })
      setShowForm(false)
      setForm(EMPTY)
      setError(null)
    },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed to create organization'),
  })

  const tree = buildTree(orgs)
  const roots = tree.get(null) ?? []

  const toggleExpand = (id: number) => {
    setExpandedIds(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const inputCls = `w-full bg-surface border border-border rounded px-3 py-2 text-sm
                    text-slate-200 placeholder-muted focus:outline-none
                    focus:border-accent/60 transition-colors`

  return (
    <div className="flex flex-col h-full p-4 gap-4 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold text-slate-100">Organizations</h1>
          <p className="text-xs text-muted mt-0.5">
            {orgs.length} nodes{isFetching && ' · refreshing...'}
          </p>
        </div>
        {canEdit && (
          <button
            onClick={() => { setShowForm(s => !s); setError(null) }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent/80
                       text-white text-sm font-medium rounded transition-colors"
          >
            {showForm ? <X size={13} /> : <Plus size={13} />}
            {showForm ? 'Cancel' : 'Add Node'}
          </button>
        )}
      </div>

      {/* Create form */}
      {showForm && (
        <form
          onSubmit={e => { e.preventDefault(); setError(null); createMut.mutate(form) }}
          className="bg-panel border border-border rounded p-4 grid grid-cols-2 gap-3 shrink-0
                     animate-[fade-in_0.2s_ease-out]"
        >
          <p className="col-span-2 text-sm font-medium text-slate-300">New organization node</p>

          <div>
            <label className="block text-xs text-muted mb-1">Code *</label>
            <input className={inputCls} required placeholder="BSNL_ROOT"
              value={form.code}
              onChange={e => setForm(f => ({ ...f, code: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Name *</label>
            <input className={inputCls} required placeholder="BSNL INDIA"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Type *</label>
            <select className={inputCls}
              value={form.type}
              onChange={e => setForm(f => ({ ...f, type: e.target.value as OrgType }))}>
              {ORG_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Parent Node</label>
            <select className={inputCls}
              value={form.parent_id ?? ''}
              onChange={e => setForm(f => ({ ...f, parent_id: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">— None (root) —</option>
              {orgs.map(o => <option key={o.id} value={o.id}>{o.code} — {o.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Circle (BSNL)</label>
            <select className={inputCls}
              value={form.circle_id ?? ''}
              onChange={e => setForm(f => ({ ...f, circle_id: e.target.value ? Number(e.target.value) : undefined, ba_id: undefined }))}>
              <option value="">— None —</option>
              {circles.map(c => <option key={c.id} value={c.id}>{c.cir_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">BA (BSNL)</label>
            <select className={inputCls} disabled={!form.circle_id}
              value={form.ba_id ?? ''}
              onChange={e => setForm(f => ({ ...f, ba_id: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">— Select circle first —</option>
              {bas.map(b => <option key={b.id} value={b.id}>{b.ba_name}</option>)}
            </select>
          </div>

          <div className="col-span-2 flex items-center justify-between">
            {error && <span className="text-xs text-alert">{error}</span>}
            <button type="submit" disabled={createMut.isPending}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent/80
                         text-white text-sm font-medium rounded transition-colors disabled:opacity-50">
              {createMut.isPending ? 'Saving...' : 'Create Node'}
            </button>
          </div>
        </form>
      )}

      {/* Tree table */}
      <div className="flex-1 bg-panel border border-border rounded overflow-hidden flex flex-col min-h-0">
        {orgs.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <Building2 size={32} className="text-dim" />
            <p className="text-sm text-slate-300">No organization nodes yet</p>
            {canEdit && <p className="text-xs text-muted">Add the ROOT node to get started</p>}
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-panel border-b border-border z-10">
                <tr className="text-muted font-mono">
                  {['Code', 'Name', 'Type', 'Status'].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {roots.map(org => (
                  <OrgNode
                    key={org.id}
                    org={org}
                    tree={tree}
                    depth={0}
                    expandedIds={expandedIds}
                    onToggle={toggleExpand}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
