import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users as UsersIcon, Plus, X, ShieldPlus, Lock, Loader2 } from 'lucide-react'
import {
  fetchUsers, createUser, fetchRoles, assignRoleToUser, removeRoleFromUser,
  fetchOrgs, fetchCircles, fetchBAs,
  type CurrentUser, type UserCreate,
} from '../api/client'
import { hasRole } from '../lib/auth'

const USER_TYPES = ['EMPLOYEE', 'CUSTOMER', 'PARTNER', 'SYSTEM']
const EMPTY: UserCreate = { username: '', password: '', user_type: 'EMPLOYEE', role: 'operator' }

function RoleChip({ code, onRemove }: { code: string; onRemove?: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 font-mono text-[10px] rounded-md px-1.5 py-0.5 transition-colors"
          style={{ background: 'oklch(0.78 0.14 200 / 0.1)', color: 'var(--color-primary)', boxShadow: '0 0 0 1px oklch(0.78 0.14 200 / 0.25)' }}>
      {code.replace(/_/g, ' ')}
      {onRemove && (
        <button onClick={onRemove} className="opacity-70 hover:opacity-100 transition-opacity" style={{ color: 'var(--color-destructive)' }}>
          <X size={9} />
        </button>
      )}
    </span>
  )
}

const inputStyle = {
  background: 'oklch(0.28 0.03 260 / 0.5)',
  color: 'var(--color-foreground)',
  boxShadow: '0 0 0 1px var(--color-border)',
} as React.CSSProperties

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-[10px] font-medium mb-1.5 uppercase tracking-widest"
             style={{ color: 'var(--color-muted-foreground)' }}>{label}</label>
      {children}
    </div>
  )
}

function UserRolePanel({ user, roles }: { user: CurrentUser; roles: { id: number; code: string }[] }) {
  const qc = useQueryClient()
  const [selectedRole, setSelectedRole] = useState('')

  const assignMut = useMutation({
    mutationFn: ({ userId, roleId }: { userId: number; roleId: number }) => assignRoleToUser(userId, roleId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); setSelectedRole('') },
  })
  const removeMut = useMutation({
    mutationFn: ({ userId, roleId }: { userId: number; roleId: number }) => removeRoleFromUser(userId, roleId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })

  const assignedCodes = new Set(user.roles)
  const unassigned = roles.filter(r => !assignedCodes.has(r.code))

  return (
    <div className="px-12 py-4" style={{ background: 'oklch(0.2 0.035 260 / 0.5)', borderTop: '1px solid var(--color-border)' }}>
      <p className="text-[10px] uppercase tracking-widest mb-2" style={{ color: 'var(--color-muted-foreground)' }}>Assigned Roles</p>
      <div className="flex flex-wrap gap-1.5 mb-4">
        {user.roles.length === 0 && <span className="text-xs italic" style={{ color: 'var(--color-dim)' }}>No roles assigned</span>}
        {user.roles.map(code => {
          const role = roles.find(r => r.code === code)
          return <RoleChip key={code} code={code} onRemove={role ? () => removeMut.mutate({ userId: user.id, roleId: role.id }) : undefined} />
        })}
      </div>
      {unassigned.length > 0 && (
        <div className="flex items-center gap-2">
          <select value={selectedRole} onChange={e => setSelectedRole(e.target.value)}
                  className="rounded-md px-3 py-1.5 text-xs outline-none w-48" style={inputStyle}>
            <option value="">Add role…</option>
            {unassigned.map(r => <option key={r.id} value={r.id}>{r.code}</option>)}
          </select>
          <button disabled={!selectedRole || assignMut.isPending}
                  onClick={() => selectedRole && assignMut.mutate({ userId: user.id, roleId: Number(selectedRole) })}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors disabled:opacity-50"
                  style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
            {assignMut.isPending ? <Loader2 size={11} className="animate-spin" /> : <ShieldPlus size={11} />}
            Assign
          </button>
        </div>
      )}
    </div>
  )
}

export default function Users() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm]         = useState<UserCreate>(EMPTY)
  const [error, setError]       = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const isAdmin = hasRole('SUPER_ADMIN')

  const { data: users = [], isFetching } = useQuery({ queryKey: ['users'], queryFn: fetchUsers, refetchInterval: 30_000, enabled: isAdmin })
  const { data: roles   = [] } = useQuery({ queryKey: ['roles'],   queryFn: fetchRoles })
  const { data: orgs    = [] } = useQuery({ queryKey: ['orgs'],    queryFn: fetchOrgs })
  const { data: circles = [] } = useQuery({ queryKey: ['circles'], queryFn: fetchCircles })
  const { data: bas     = [] } = useQuery({ queryKey: ['bas', form.circle_id], queryFn: () => fetchBAs(form.circle_id), enabled: !!form.circle_id })

  const createMut = useMutation({
    mutationFn: createUser,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); setShowForm(false); setForm(EMPTY); setError(null) },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed to create user'),
  })

  const toggleExpand = (id: number) => {
    setExpanded(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next })
  }

  const inputCls = "w-full rounded-lg px-3 py-2 text-sm outline-none transition-all disabled:opacity-50"

  if (!isAdmin) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 h-full animate-[fade-in_0.2s_ease-out]">
        <Lock size={32} style={{ color: 'var(--color-dim)' }} />
        <p className="text-sm" style={{ color: 'var(--color-foreground)' }}>SUPER_ADMIN role required</p>
        <p className="text-xs" style={{ color: 'var(--color-muted-foreground)' }}>Contact your administrator for access.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full p-4 lg:p-6 gap-5 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold flex items-center gap-2" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            <UsersIcon size={16} style={{ color: 'var(--color-primary)' }} /> Users
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
            {users.length} accounts{isFetching && ' · refreshing...'}
          </p>
        </div>
        <button onClick={() => { setShowForm(s => !s); setError(null) }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
                style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
          {showForm ? <X size={13} /> : <Plus size={13} />}
          {showForm ? 'Cancel' : 'Add User'}
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form onSubmit={e => { e.preventDefault(); setError(null); createMut.mutate(form) }}
              className="rounded-2xl p-5 grid grid-cols-3 gap-4 shrink-0 animate-[fade-in_0.2s_ease-out]"
              style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
          <p className="col-span-3 text-sm font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            New user account
          </p>
          {[
            { label: 'Username *', field: 'username', type: 'text',     placeholder: 'john.doe', required: true },
            { label: 'Password *', field: 'password', type: 'password', placeholder: '••••••••', required: true },
            { label: 'Email',      field: 'email',    type: 'email',    placeholder: 'john@bsnl.in' },
            { label: 'Mobile',     field: 'mobile',   type: 'text',     placeholder: '+91 98765...' },
            { label: 'First Name', field: 'first_name', type: 'text',   placeholder: 'John' },
            { label: 'Last Name',  field: 'last_name',  type: 'text',   placeholder: 'Doe' },
          ].map(({ label, field, type, placeholder, required }) => (
            <Field key={field} label={label}>
              <input className={inputCls} style={inputStyle} type={type} placeholder={placeholder} required={!!required}
                     value={(form as any)[field] ?? ''} onChange={e => setForm(f => ({ ...f, [field]: e.target.value || undefined }))} />
            </Field>
          ))}
          <Field label="User Type">
            <select className={inputCls} style={inputStyle} value={form.user_type ?? 'EMPLOYEE'} onChange={e => setForm(f => ({ ...f, user_type: e.target.value }))}>
              {USER_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
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
          <div className="col-span-3 flex items-center justify-between mt-2">
            {error && <span className="text-xs" style={{ color: 'var(--color-destructive)' }}>{error}</span>}
            <button type="submit" disabled={createMut.isPending}
                    className="ml-auto px-4 py-2 rounded-lg text-sm font-semibold transition-all disabled:opacity-50"
                    style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
              {createMut.isPending ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="flex-1 rounded-2xl overflow-hidden flex flex-col min-h-0"
           style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
        {users.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <UsersIcon size={32} style={{ color: 'var(--color-dim)' }} />
            <p className="text-sm" style={{ color: 'var(--color-foreground)' }}>No users found</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="text-[11px] font-medium uppercase tracking-widest sticky top-0"
                    style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)', background: 'oklch(0.22 0.035 260)' }}>
                  {['', 'Username', 'Email', 'Type', 'Roles', 'Status'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <>
                    <tr key={user.id}
                        className="cursor-pointer transition-colors last:border-b-0"
                        style={{ borderBottom: '1px solid var(--color-border)' }}
                        onClick={() => toggleExpand(user.id)}
                        onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)')}
                        onMouseOut={e => (e.currentTarget.style.background = 'transparent')}>
                      <td className="px-4 py-3 w-8">
                        <ShieldPlus size={14} style={{ color: expanded.has(user.id) ? 'var(--color-primary)' : 'var(--color-muted-foreground)' }} />
                      </td>
                      <td className="px-4 py-3 font-mono font-medium" style={{ color: 'var(--color-foreground)' }}>
                        {user.username}
                        {user.is_locked && <Lock size={10} className="inline ml-1.5" style={{ color: 'var(--color-destructive)' }} />}
                      </td>
                      <td className="px-4 py-3" style={{ color: 'var(--color-muted-foreground)' }}>{user.email ?? '—'}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-mono tracking-wide"
                              style={{ background: 'oklch(0.78 0.14 200 / 0.1)', color: 'var(--color-primary)', boxShadow: '0 0 0 1px oklch(0.78 0.14 200 / 0.25)' }}>
                          {user.user_type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1.5">
                          {user.roles.slice(0, 3).map(r => <RoleChip key={r} code={r} />)}
                          {user.roles.length > 3 && (
                            <span className="text-[10px]" style={{ color: 'var(--color-muted-foreground)' }}>+{user.roles.length - 3}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-block size-1.5 rounded-full" style={{ background: user.is_active ? 'var(--color-success)' : 'var(--color-dim)' }} />
                      </td>
                    </tr>
                    {expanded.has(user.id) && (
                      <tr key={`roles-${user.id}`}>
                        <td colSpan={6} className="p-0">
                          <UserRolePanel user={user} roles={roles} />
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
