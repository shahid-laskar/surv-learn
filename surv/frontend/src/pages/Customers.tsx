import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { UserCog, Plus, X, ChevronDown, ChevronRight, MapPin, Loader2 } from 'lucide-react'
import {
  fetchCustomers, createCustomer, fetchCustomerSites, createCustomerSite,
  fetchOrgs, fetchCircles, fetchBAs,
  type CustomerCreate, type CustomerSiteCreate, type CustomerType,
} from '../api/client'
import { hasPermission, hasRole } from '../lib/auth'

const CUSTOMER_TYPES: CustomerType[] = ['ENTERPRISE', 'BANK', 'SCHOOL', 'HOSPITAL', 'APARTMENT', 'GOVERNMENT', 'INDIVIDUAL', 'PARTNER']

const TYPE_COLORS: Record<CustomerType, { bg: string, color: string }> = {
  ENTERPRISE:  { bg: 'oklch(0.55 0.15 250 / 0.1)', color: 'oklch(0.55 0.15 250)' },
  BANK:        { bg: 'oklch(0.72 0.17 150 / 0.1)', color: 'var(--color-success)' },
  SCHOOL:      { bg: 'oklch(0.78 0.15 75 / 0.1)', color: 'var(--color-warning)' },
  HOSPITAL:    { bg: 'oklch(0.62 0.22 25 / 0.1)', color: 'var(--color-destructive)' },
  APARTMENT:   { bg: 'oklch(0.65 0.18 290 / 0.1)', color: 'oklch(0.65 0.18 290)' },
  GOVERNMENT:  { bg: 'oklch(0.78 0.14 200 / 0.1)', color: 'var(--color-primary)' },
  INDIVIDUAL:  { bg: 'oklch(0.6 0.15 45 / 0.1)', color: 'oklch(0.6 0.15 45)' },
  PARTNER:     { bg: 'oklch(0.78 0.14 200 / 0.15)', color: 'var(--color-primary)' },
}

const EMPTY_CUSTOMER: CustomerCreate = { name: '' }
const EMPTY_SITE: CustomerSiteCreate = {}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium mb-1.5 uppercase tracking-widest"
             style={{ color: 'var(--color-muted-foreground)' }}>{label}</label>
      {children}
    </div>
  )
}

const inputStyle = {
  background: 'oklch(0.28 0.03 260 / 0.5)',
  color: 'var(--color-foreground)',
  boxShadow: '0 0 0 1px var(--color-border)',
} as React.CSSProperties

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
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['customer-sites', customerId] }); setShowAdd(false); setForm(EMPTY_SITE); setError(null) },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed to create site'),
  })

  const inputCls = "w-full rounded-md px-3 py-1.5 text-xs outline-none transition-all disabled:opacity-50"

  return (
    <div className="px-12 py-4" style={{ background: 'oklch(0.2 0.035 260 / 0.5)', borderTop: '1px solid var(--color-border)' }}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-[10px] font-mono uppercase tracking-widest" style={{ color: 'var(--color-muted-foreground)' }}>
          Sites {isFetching ? '(loading…)' : `(${sites.length})`}
        </p>
        {canEdit && (
          <button onClick={() => setShowAdd(s => !s)}
                  className="flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors"
                  style={{ color: 'var(--color-primary)' }}
                  onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.78 0.14 200 / 0.1)')}
                  onMouseOut={e => (e.currentTarget.style.background = 'transparent')}>
            {showAdd ? <X size={11} /> : <Plus size={11} />}
            {showAdd ? 'Cancel' : 'Add site'}
          </button>
        )}
      </div>

      {showAdd && (
        <form onSubmit={e => { e.preventDefault(); createMut.mutate(form) }}
              className="grid grid-cols-3 gap-3 mb-4 p-4 rounded-xl animate-[fade-in_0.15s_ease-out]"
              style={{ background: 'var(--color-panel)', boxShadow: '0 0 0 1px var(--color-border)' }}>
          {(['name','site_code','city','district','state'] as const).map(field => (
            <div key={field}>
              <label className="block text-[10px] uppercase tracking-widest mb-1.5" style={{ color: 'var(--color-muted-foreground)' }}>{field.replace('_', ' ')}</label>
              <input className={inputCls} style={inputStyle} placeholder={field}
                     value={(form as any)[field] ?? ''} onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))} />
            </div>
          ))}
          <div className="col-span-3 flex items-center justify-between mt-2">
            {error && <span className="text-xs" style={{ color: 'var(--color-destructive)' }}>{error}</span>}
            <button type="submit" disabled={createMut.isPending}
                    className="ml-auto flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors disabled:opacity-50"
                    style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
              {createMut.isPending && <Loader2 size={11} className="animate-spin" />} Save site
            </button>
          </div>
        </form>
      )}

      {sites.length === 0 && !showAdd ? (
        <p className="text-xs italic" style={{ color: 'var(--color-dim)' }}>No sites added yet</p>
      ) : (
        <div className="space-y-1.5">
          {sites.map(site => (
            <div key={site.id} className="flex items-center gap-3 rounded-lg px-3 py-2 text-xs" style={{ background: 'var(--color-panel)' }}>
              <MapPin size={11} style={{ color: 'var(--color-muted-foreground)' }} />
              <span className="font-mono" style={{ color: 'var(--color-muted-foreground)' }}>{site.site_code ?? '—'}</span>
              <span className="font-medium" style={{ color: 'var(--color-foreground)' }}>{site.name ?? 'Unnamed site'}</span>
              {site.city && <span style={{ color: 'var(--color-muted-foreground)' }}>{site.city}</span>}
              {site.district && <span style={{ color: 'var(--color-muted-foreground)' }}>{site.district}</span>}
              {site.state && <span style={{ color: 'var(--color-muted-foreground)' }}>{site.state}</span>}
              <span className="ml-auto size-1.5 rounded-full" style={{ background: site.is_active ? 'var(--color-success)' : 'var(--color-dim)' }} />
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

  const { data: customers = [], isFetching } = useQuery({ queryKey: ['customers'], queryFn: fetchCustomers, refetchInterval: 30_000 })
  const { data: orgs    = [] } = useQuery({ queryKey: ['orgs'],    queryFn: fetchOrgs })
  const { data: circles = [] } = useQuery({ queryKey: ['circles'], queryFn: fetchCircles })
  const { data: bas     = [] } = useQuery({ queryKey: ['bas', form.circle_id], queryFn: () => fetchBAs(form.circle_id), enabled: !!form.circle_id })

  const createMut = useMutation({
    mutationFn: createCustomer,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['customers'] }); setShowForm(false); setForm(EMPTY_CUSTOMER); setError(null) },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed to create customer'),
  })

  const toggleExpand = (id: number) => {
    setExpanded(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next })
  }

  const inputCls = "w-full rounded-lg px-3 py-2 text-sm outline-none transition-all disabled:opacity-50"

  return (
    <div className="flex flex-col h-full p-4 lg:p-6 gap-5 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold flex items-center gap-2" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            <UserCog size={16} style={{ color: 'var(--color-primary)' }} /> Customers
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
            {customers.length} registered{isFetching && ' · refreshing...'}
          </p>
        </div>
        {canEdit && (
          <button onClick={() => { setShowForm(s => !s); setError(null) }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
                  style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
            {showForm ? <X size={13} /> : <Plus size={13} />}
            {showForm ? 'Cancel' : 'Add Customer'}
          </button>
        )}
      </div>

      {/* Create form */}
      {showForm && (
        <form onSubmit={e => { e.preventDefault(); setError(null); createMut.mutate(form) }}
              className="rounded-2xl p-5 grid grid-cols-2 gap-4 shrink-0 animate-[fade-in_0.2s_ease-out]"
              style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
          <p className="col-span-2 text-sm font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            New customer
          </p>
          <Field label="Name *">
            <input className={inputCls} style={inputStyle} required placeholder="Acme Corp" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </Field>
          <Field label="Customer Code">
            <input className={inputCls} style={inputStyle} placeholder="CUST001" value={form.customer_code ?? ''} onChange={e => setForm(f => ({ ...f, customer_code: e.target.value || undefined }))} />
          </Field>
          <Field label="Type">
            <select className={inputCls} style={inputStyle} value={form.customer_type ?? ''} onChange={e => setForm(f => ({ ...f, customer_type: (e.target.value as CustomerType) || undefined }))}>
              <option value="">— Select type —</option>
              {CUSTOMER_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="Organization">
            <select className={inputCls} style={inputStyle} value={form.organization_id ?? ''} onChange={e => setForm(f => ({ ...f, organization_id: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">— None —</option>
              {orgs.map(o => <option key={o.id} value={o.id}>{o.code} — {o.name}</option>)}
            </select>
          </Field>
          <Field label="Circle">
            <select className={inputCls} style={inputStyle} value={form.circle_id ?? ''} onChange={e => setForm(f => ({ ...f, circle_id: e.target.value ? Number(e.target.value) : undefined, ba_id: undefined }))}>
              <option value="">— None —</option>
              {circles.map(c => <option key={c.id} value={c.id}>{c.cir_name}</option>)}
            </select>
          </Field>
          <Field label="BA">
            <select className={inputCls} style={inputStyle} disabled={!form.circle_id} value={form.ba_id ?? ''} onChange={e => setForm(f => ({ ...f, ba_id: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">— Select circle first —</option>
              {bas.map(b => <option key={b.id} value={b.id}>{b.ba_name}</option>)}
            </select>
          </Field>
          <Field label="Email">
            <input className={inputCls} style={inputStyle} type="email" placeholder="billing@company.com" value={form.email ?? ''} onChange={e => setForm(f => ({ ...f, email: e.target.value || undefined }))} />
          </Field>
          <Field label="Phone">
            <input className={inputCls} style={inputStyle} placeholder="+91 98765 43210" value={form.phone ?? ''} onChange={e => setForm(f => ({ ...f, phone: e.target.value || undefined }))} />
          </Field>
          <div className="col-span-2 flex items-center justify-between mt-2">
            {error && <span className="text-xs" style={{ color: 'var(--color-destructive)' }}>{error}</span>}
            <button type="submit" disabled={createMut.isPending}
                    className="ml-auto px-4 py-2 rounded-lg text-sm font-semibold transition-all disabled:opacity-50"
                    style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
              {createMut.isPending ? 'Saving...' : 'Create Customer'}
            </button>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="flex-1 rounded-2xl overflow-hidden flex flex-col min-h-0"
           style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
        {customers.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <UserCog size={32} style={{ color: 'var(--color-dim)' }} />
            <p className="text-sm" style={{ color: 'var(--color-foreground)' }}>No customers yet</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="text-[11px] font-medium uppercase tracking-widest sticky top-0"
                    style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)', background: 'oklch(0.22 0.035 260)' }}>
                  {['', 'Name', 'Code', 'Type', 'Contact', 'Status'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {customers.map(cust => (
                  <>
                    <tr key={cust.id}
                        className="cursor-pointer transition-colors last:border-b-0"
                        style={{ borderBottom: '1px solid var(--color-border)' }}
                        onClick={() => toggleExpand(cust.id)}
                        onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)')}
                        onMouseOut={e => (e.currentTarget.style.background = 'transparent')}>
                      <td className="px-4 py-3 w-8">
                        {expanded.has(cust.id)
                          ? <ChevronDown size={14} style={{ color: 'var(--color-muted-foreground)' }} />
                          : <ChevronRight size={14} style={{ color: 'var(--color-muted-foreground)' }} />}
                      </td>
                      <td className="px-4 py-3 font-medium" style={{ color: 'var(--color-foreground)' }}>{cust.name}</td>
                      <td className="px-4 py-3 font-mono" style={{ color: 'var(--color-muted-foreground)' }}>{cust.customer_code ?? '—'}</td>
                      <td className="px-4 py-3">
                        {cust.customer_type ? (() => {
                          const t = TYPE_COLORS[cust.customer_type as CustomerType] || { bg: 'var(--color-secondary)', color: 'var(--color-muted-foreground)' }
                          return (
                            <span className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-mono tracking-wide"
                                  style={{ background: t.bg, color: t.color, boxShadow: `0 0 0 1px ${t.bg.replace('0.1', '0.25')}` }}>
                              {cust.customer_type}
                            </span>
                          )
                        })() : <span style={{ color: 'var(--color-dim)' }}>—</span>}
                      </td>
                      <td className="px-4 py-3" style={{ color: 'var(--color-muted-foreground)' }}>{cust.email ?? cust.phone ?? '—'}</td>
                      <td className="px-4 py-3">
                        <span className="inline-block size-1.5 rounded-full" style={{ background: cust.is_active ? 'var(--color-success)' : 'var(--color-dim)' }} />
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
