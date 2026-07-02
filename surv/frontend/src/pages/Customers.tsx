import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { UserCog, Plus, X, ChevronDown, ChevronRight, MapPin } from 'lucide-react'
import {
  fetchCustomers, createCustomer, fetchCustomerSites, createCustomerSite,
  fetchOrgs, fetchCircles, fetchBAs,
  type CustomerCreate, type CustomerSiteCreate, type CustomerType,
} from '../api/client'
import { hasPermission, hasRole } from '../lib/auth'

const CUSTOMER_TYPES: CustomerType[] = ['ENTERPRISE', 'BANK', 'SCHOOL', 'HOSPITAL', 'APARTMENT', 'GOVERNMENT', 'INDIVIDUAL', 'PARTNER']

const TYPE_COLORS: Record<CustomerType, string> = {
  ENTERPRISE:  'bg-blue-500/20 text-blue-300',
  BANK:        'bg-green-500/20 text-green-300',
  SCHOOL:      'bg-yellow-500/20 text-yellow-300',
  HOSPITAL:    'bg-red-500/20 text-red-300',
  APARTMENT:   'bg-purple-500/20 text-purple-300',
  GOVERNMENT:  'bg-cyan-500/20 text-cyan-300',
  INDIVIDUAL:  'bg-orange-500/20 text-orange-300',
  PARTNER:     'bg-teal-500/20 text-teal-300',
}

const EMPTY_CUSTOMER: CustomerCreate = { name: '' }
const EMPTY_SITE: CustomerSiteCreate = {}

function SitesPanel({ customerId }: { customerId: number }) {
  const qc = useQueryClient()
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm]       = useState<CustomerSiteCreate>(EMPTY_SITE)
  const [error, setError]     = useState<string | null>(null)
  const canEdit = hasPermission('customer.update') || hasRole('SUPER_ADMIN')

  const { data: sites = [], isFetching } = useQuery({
    queryKey: ['customer-sites', customerId],
    queryFn:  () => fetchCustomerSites(customerId),
  })

  const createMut = useMutation({
    mutationFn: (payload: CustomerSiteCreate) => createCustomerSite(customerId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['customer-sites', customerId] })
      setShowAdd(false)
      setForm(EMPTY_SITE)
      setError(null)
    },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed to create site'),
  })

  const inputCls = `w-full bg-surface border border-border rounded px-3 py-1.5 text-xs
                    text-slate-200 placeholder-muted focus:outline-none focus:border-accent/60 transition-colors`

  return (
    <div className="px-12 py-3 bg-surface/50 border-t border-border/30">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-muted font-mono uppercase tracking-wider">
          Sites {isFetching ? '(loading…)' : `(${sites.length})`}
        </p>
        {canEdit && (
          <button onClick={() => setShowAdd(s => !s)}
            className="flex items-center gap-1 text-xs text-accent hover:text-accent/70 transition-colors">
            {showAdd ? <X size={11} /> : <Plus size={11} />}
            {showAdd ? 'Cancel' : 'Add site'}
          </button>
        )}
      </div>

      {showAdd && (
        <form onSubmit={e => { e.preventDefault(); createMut.mutate(form) }}
          className="grid grid-cols-3 gap-2 mb-3 p-3 bg-panel border border-border/50 rounded animate-[fade-in_0.15s_ease-out]">
          {(['name','site_code','city','district','state'] as const).map(field => (
            <div key={field}>
              <label className="block text-[10px] text-muted mb-1 capitalize">{field.replace('_', ' ')}</label>
              <input className={inputCls} placeholder={field}
                value={(form as any)[field] ?? ''}
                onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))} />
            </div>
          ))}
          <div className="col-span-3 flex items-center justify-between mt-1">
            {error && <span className="text-xs text-alert">{error}</span>}
            <button type="submit" disabled={createMut.isPending}
              className="ml-auto px-3 py-1 bg-accent/80 hover:bg-accent text-white text-xs rounded transition-colors disabled:opacity-50">
              {createMut.isPending ? 'Saving...' : 'Save site'}
            </button>
          </div>
        </form>
      )}

      {sites.length === 0 && !showAdd ? (
        <p className="text-xs text-muted/60 italic">No sites added yet</p>
      ) : (
        <div className="space-y-1">
          {sites.map(site => (
            <div key={site.id}
              className="flex items-center gap-3 text-xs text-slate-400 py-1">
              <MapPin size={11} className="text-muted shrink-0" />
              <span className="font-mono text-muted">{site.site_code ?? '—'}</span>
              <span className="text-slate-300">{site.name ?? 'Unnamed site'}</span>
              {site.city && <span className="text-muted">{site.city}</span>}
              {site.district && <span className="text-muted">{site.district}</span>}
              {site.state && <span className="text-muted">{site.state}</span>}
              <span className={`ml-auto size-1.5 rounded-full ${site.is_active ? 'bg-online' : 'bg-dim'}`} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Customers() {
  const qc = useQueryClient()
  const [showForm, setShowForm]   = useState(false)
  const [form, setForm]           = useState<CustomerCreate>(EMPTY_CUSTOMER)
  const [error, setError]         = useState<string | null>(null)
  const [expanded, setExpanded]   = useState<Set<number>>(new Set())

  const canEdit = hasPermission('customer.create') || hasRole('SUPER_ADMIN')

  const { data: customers = [], isFetching } = useQuery({
    queryKey:        ['customers'],
    queryFn:         fetchCustomers,
    refetchInterval: 30_000,
  })

  const { data: orgs    = [] } = useQuery({ queryKey: ['orgs'],    queryFn: fetchOrgs })
  const { data: circles = [] } = useQuery({ queryKey: ['circles'], queryFn: fetchCircles })
  const { data: bas     = [] } = useQuery({
    queryKey: ['bas', form.circle_id],
    queryFn:  () => fetchBAs(form.circle_id),
    enabled:  !!form.circle_id,
  })

  const createMut = useMutation({
    mutationFn: createCustomer,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['customers'] })
      setShowForm(false)
      setForm(EMPTY_CUSTOMER)
      setError(null)
    },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed to create customer'),
  })

  const toggleExpand = (id: number) => {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const inputCls = `w-full bg-surface border border-border rounded px-3 py-2 text-sm
                    text-slate-200 placeholder-muted focus:outline-none focus:border-accent/60 transition-colors`

  return (
    <div className="flex flex-col h-full p-4 gap-4 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold text-slate-100">Customers</h1>
          <p className="text-xs text-muted mt-0.5">
            {customers.length} registered{isFetching && ' · refreshing...'}
          </p>
        </div>
        {canEdit && (
          <button
            onClick={() => { setShowForm(s => !s); setError(null) }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent/80
                       text-white text-sm font-medium rounded transition-colors"
          >
            {showForm ? <X size={13} /> : <Plus size={13} />}
            {showForm ? 'Cancel' : 'Add Customer'}
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
          <p className="col-span-2 text-sm font-medium text-slate-300">New customer</p>

          <div>
            <label className="block text-xs text-muted mb-1">Name *</label>
            <input className={inputCls} required placeholder="Acme Corp"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Customer Code</label>
            <input className={inputCls} placeholder="CUST001"
              value={form.customer_code ?? ''}
              onChange={e => setForm(f => ({ ...f, customer_code: e.target.value || undefined }))} />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Type</label>
            <select className={inputCls}
              value={form.customer_type ?? ''}
              onChange={e => setForm(f => ({ ...f, customer_type: (e.target.value as CustomerType) || undefined }))}>
              <option value="">— Select type —</option>
              {CUSTOMER_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Organization</label>
            <select className={inputCls}
              value={form.organization_id ?? ''}
              onChange={e => setForm(f => ({ ...f, organization_id: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">— None —</option>
              {orgs.map(o => <option key={o.id} value={o.id}>{o.code} — {o.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Circle</label>
            <select className={inputCls}
              value={form.circle_id ?? ''}
              onChange={e => setForm(f => ({ ...f, circle_id: e.target.value ? Number(e.target.value) : undefined, ba_id: undefined }))}>
              <option value="">— None —</option>
              {circles.map(c => <option key={c.id} value={c.id}>{c.cir_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">BA</label>
            <select className={inputCls} disabled={!form.circle_id}
              value={form.ba_id ?? ''}
              onChange={e => setForm(f => ({ ...f, ba_id: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">— Select circle first —</option>
              {bas.map(b => <option key={b.id} value={b.id}>{b.ba_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Email</label>
            <input className={inputCls} type="email" placeholder="billing@company.com"
              value={form.email ?? ''}
              onChange={e => setForm(f => ({ ...f, email: e.target.value || undefined }))} />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Phone</label>
            <input className={inputCls} placeholder="+91 98765 43210"
              value={form.phone ?? ''}
              onChange={e => setForm(f => ({ ...f, phone: e.target.value || undefined }))} />
          </div>

          <div className="col-span-2 flex items-center justify-between">
            {error && <span className="text-xs text-alert">{error}</span>}
            <button type="submit" disabled={createMut.isPending}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent/80
                         text-white text-sm font-medium rounded transition-colors disabled:opacity-50">
              {createMut.isPending ? 'Saving...' : 'Create Customer'}
            </button>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="flex-1 bg-panel border border-border rounded overflow-hidden flex flex-col min-h-0">
        {customers.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <UserCog size={32} className="text-dim" />
            <p className="text-sm text-slate-300">No customers yet</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-panel border-b border-border z-10">
                <tr className="text-muted font-mono">
                  {['', 'Name', 'Code', 'Type', 'Contact', 'Status'].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {customers.map(cust => (
                  <>
                    <tr key={cust.id}
                      className="border-b border-border/50 hover:bg-border/20 transition-colors cursor-pointer"
                      onClick={() => toggleExpand(cust.id)}>
                      <td className="px-4 py-3 w-8">
                        {expanded.has(cust.id)
                          ? <ChevronDown size={12} className="text-muted" />
                          : <ChevronRight size={12} className="text-muted" />
                        }
                      </td>
                      <td className="px-4 py-3 text-slate-200 font-medium">{cust.name}</td>
                      <td className="px-4 py-3 font-mono text-muted">{cust.customer_code ?? '—'}</td>
                      <td className="px-4 py-3">
                        {cust.customer_type ? (
                          <span className={`font-mono text-[10px] px-2 py-0.5 rounded ${TYPE_COLORS[cust.customer_type as CustomerType] ?? 'bg-dim/20 text-muted'}`}>
                            {cust.customer_type}
                          </span>
                        ) : <span className="text-dim">—</span>}
                      </td>
                      <td className="px-4 py-3 text-muted">{cust.email ?? cust.phone ?? '—'}</td>
                      <td className="px-4 py-3">
                        <span className={`size-1.5 rounded-full inline-block ${cust.is_active ? 'bg-online' : 'bg-dim'}`} />
                      </td>
                    </tr>
                    {expanded.has(cust.id) && (
                      <tr key={`sites-${cust.id}`}>
                        <td colSpan={6} className="p-0">
                          <SitesPanel customerId={cust.id} />
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
