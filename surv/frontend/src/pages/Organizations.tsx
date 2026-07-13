import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Building2, Plus, X, ChevronRight, ChevronDown, GitBranch } from 'lucide-react'
import {
  fetchOrgs, createOrg, fetchCircles, fetchBAs,
  type Organization, type OrganizationCreate, type OrgType,
} from '../api/client'
import { hasPermission, hasRole } from '../lib/auth'

const ORG_TYPES: OrgType[] = ['ROOT', 'CIRCLE', 'BA', 'SSA', 'DISTRICT', 'SITE', 'NOC']

const TYPE_COLORS: Record<OrgType, { bg: string, color: string }> = {
  ROOT:     { bg: 'oklch(0.65 0.18 290 / 0.1)', color: 'oklch(0.65 0.18 290)' },
  CIRCLE:   { bg: 'oklch(0.55 0.15 250 / 0.1)', color: 'oklch(0.55 0.15 250)' },
  BA:       { bg: 'oklch(0.72 0.17 150 / 0.1)', color: 'var(--color-success)' },
  SSA:      { bg: 'oklch(0.78 0.14 200 / 0.1)', color: 'var(--color-primary)' },
  DISTRICT: { bg: 'oklch(0.62 0.22 25 / 0.1)', color: 'var(--color-destructive)' },
  SITE:     { bg: 'oklch(0.78 0.15 75 / 0.1)', color: 'var(--color-warning)' },
  NOC:      { bg: 'oklch(0.6 0.15 45 / 0.1)', color: 'oklch(0.6 0.15 45)' },
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

function OrgNode({ org, tree, depth, expandedIds, onToggle }: {
  org: Organization; tree: Map<number | null, Organization[]>; depth: number
  expandedIds: Set<number>; onToggle: (id: number) => void
}) {
  const children = tree.get(org.id) ?? []
  const hasChildren = children.length > 0
  const isExpanded = expandedIds.has(org.id)
  const tone = TYPE_COLORS[org.type as OrgType] ?? { bg: 'var(--color-secondary)', color: 'var(--color-muted-foreground)' }

  return (
    <>
      <tr className="transition-colors last:border-b-0"
          style={{ borderBottom: '1px solid var(--color-border)' }}
          onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)')}
          onMouseOut={e => (e.currentTarget.style.background = 'transparent')}>
        <td className="px-4 py-3 w-[300px]">
          <div className="flex items-center gap-2" style={{ paddingLeft: `${depth * 20}px` }}>
            <button
              onClick={() => onToggle(org.id)}
              className={`flex size-5 shrink-0 items-center justify-center rounded-md transition-colors ${
                hasChildren ? 'hover:bg-white/5 cursor-pointer text-muted-foreground' : 'cursor-default text-dim'
              }`}
              style={{ color: hasChildren ? 'var(--color-muted-foreground)' : 'var(--color-dim)' }}
            >
              {hasChildren ? (isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />)
                         : <span className="size-1.5 rounded-full" style={{ background: 'var(--color-dim)' }} />}
            </button>
            <GitBranch size={13} style={{ color: 'var(--color-muted-foreground)' }} />
            <span className="font-mono text-xs font-semibold" style={{ color: 'var(--color-foreground)' }}>{org.code}</span>
          </div>
        </td>
        <td className="px-4 py-3 text-sm" style={{ color: 'var(--color-muted-foreground)' }}>{org.name}</td>
        <td className="px-4 py-3">
          <span className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-mono tracking-wide"
                style={{ background: tone.bg, color: tone.color, boxShadow: `0 0 0 1px ${tone.bg.replace('0.1', '0.25')}` }}>
            {org.type}
          </span>
        </td>
        <td className="px-4 py-3">
          <span className="inline-block size-1.5 rounded-full"
                style={{ background: org.is_active ? 'var(--color-success)' : 'var(--color-dim)' }} />
        </td>
      </tr>
      {isExpanded && children.map(child => (
        <OrgNode key={child.id} org={child} tree={tree} depth={depth + 1}
                 expandedIds={expandedIds} onToggle={onToggle} />
      ))}
    </>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium mb-1.5 uppercase tracking-widest"
             style={{ color: 'var(--color-muted-foreground)' }}>
        {label}
      </label>
      {children}
    </div>
  )
}

const inputStyle = {
  background: 'oklch(0.28 0.03 260 / 0.5)',
  color: 'var(--color-foreground)',
  boxShadow: '0 0 0 1px var(--color-border)',
} as React.CSSProperties

export default function Organizations() {
  const qc = useQueryClient()
  const [showForm, setShowForm]       = useState(false)
  const [form, setForm]               = useState<OrganizationCreate>(EMPTY)
  const [error, setError]             = useState<string | null>(null)
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())

  const canEdit = hasPermission('system.settings') || hasRole('SUPER_ADMIN')

  const { data: orgs = [], isFetching } = useQuery({ queryKey: ['orgs'], queryFn: fetchOrgs, refetchInterval: 30_000 })
  const { data: circles = [] } = useQuery({ queryKey: ['circles'], queryFn: fetchCircles })
  const { data: bas = [] }     = useQuery({ queryKey: ['bas', form.circle_id], queryFn: () => fetchBAs(form.circle_id), enabled: !!form.circle_id })

  const createMut = useMutation({
    mutationFn: createOrg,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['orgs'] }); setShowForm(false); setForm(EMPTY); setError(null) },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed to create organization'),
  })

  const tree = buildTree(orgs)
  const roots = tree.get(null) ?? []

  const toggleExpand = (id: number) => {
    setExpandedIds(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next })
  }

  const inputCls = "w-full rounded-lg px-3 py-2 text-sm outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"

  return (
    <div className="flex flex-col h-full p-4 lg:p-6 gap-5 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold flex items-center gap-2"
              style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            <Building2 size={16} style={{ color: 'var(--color-primary)' }} />
            Organizations
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
            {orgs.length} nodes{isFetching && ' · refreshing...'}
          </p>
        </div>
        {canEdit && (
          <button onClick={() => { setShowForm(s => !s); setError(null) }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
                  style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
            {showForm ? <X size={13} /> : <Plus size={13} />}
            {showForm ? 'Cancel' : 'Add Node'}
          </button>
        )}
      </div>

      {/* Create form */}
      {showForm && (
        <form onSubmit={e => { e.preventDefault(); setError(null); createMut.mutate(form) }}
              className="rounded-2xl p-5 grid grid-cols-2 gap-4 shrink-0 animate-[fade-in_0.2s_ease-out]"
              style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
          <p className="col-span-2 text-sm font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            New organization node
          </p>
          <Field label="Code *">
            <input className={inputCls} style={inputStyle} required placeholder="BSNL_ROOT" value={form.code} onChange={e => setForm(f => ({ ...f, code: e.target.value }))} />
          </Field>
          <Field label="Name *">
            <input className={inputCls} style={inputStyle} required placeholder="BSNL INDIA" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </Field>
          <Field label="Type *">
            <select className={inputCls} style={inputStyle} value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value as OrgType }))}>
              {ORG_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="Parent Node">
            <select className={inputCls} style={inputStyle} value={form.parent_id ?? ''} onChange={e => setForm(f => ({ ...f, parent_id: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">— None (root) —</option>
              {orgs.map(o => <option key={o.id} value={o.id}>{o.code} — {o.name}</option>)}
            </select>
          </Field>
          <Field label="Circle (BSNL)">
            <select className={inputCls} style={inputStyle} value={form.circle_id ?? ''} onChange={e => setForm(f => ({ ...f, circle_id: e.target.value ? Number(e.target.value) : undefined, ba_id: undefined }))}>
              <option value="">— None —</option>
              {circles.map(c => <option key={c.id} value={c.id}>{c.cir_name}</option>)}
            </select>
          </Field>
          <Field label="BA (BSNL)">
            <select className={inputCls} style={inputStyle} disabled={!form.circle_id} value={form.ba_id ?? ''} onChange={e => setForm(f => ({ ...f, ba_id: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">— Select circle first —</option>
              {bas.map(b => <option key={b.id} value={b.id}>{b.ba_name}</option>)}
            </select>
          </Field>
          <div className="col-span-2 flex items-center justify-between mt-2">
            {error && <span className="text-xs" style={{ color: 'var(--color-destructive)' }}>{error}</span>}
            <button type="submit" disabled={createMut.isPending}
                    className="ml-auto px-4 py-2 rounded-lg text-sm font-semibold transition-all disabled:opacity-50"
                    style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
              {createMut.isPending ? 'Saving...' : 'Create Node'}
            </button>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="flex-1 rounded-2xl overflow-hidden flex flex-col min-h-0"
           style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
        {orgs.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <Building2 size={32} style={{ color: 'var(--color-dim)' }} />
            <p className="text-sm" style={{ color: 'var(--color-foreground)' }}>No organization nodes yet</p>
            {canEdit && <p className="text-xs" style={{ color: 'var(--color-muted-foreground)' }}>Add the ROOT node to get started</p>}
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="text-[11px] font-medium uppercase tracking-widest sticky top-0"
                    style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)', background: 'oklch(0.22 0.035 260)' }}>
                  {['Code', 'Name', 'Type', 'Status'].map(h => (
                    <th key={h} className="px-4 py-3 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {roots.map(org => <OrgNode key={org.id} org={org} tree={tree} depth={0} expandedIds={expandedIds} onToggle={toggleExpand} />)}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
