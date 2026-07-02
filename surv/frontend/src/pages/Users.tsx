import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users as UsersIcon, Plus, X, ShieldPlus, Lock } from 'lucide-react'
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
    <span className="inline-flex items-center gap-1 font-mono text-[10px] bg-accent/10 text-accent
                     border border-accent/20 px-1.5 py-0.5 rounded">
      {code.replace(/_/g, ' ')}
      {onRemove && (
        <button onClick={onRemove} className="text-accent/60 hover:text-alert transition-colors">
          <X size={9} />
        </button>
      )}
    </span>
  )
}

function UserRolePanel({ user, roles }: { user: CurrentUser; roles: { id: number; code: string }[] }) {
  const qc = useQueryClient()
  const [selectedRole, setSelectedRole] = useState('')

  const assignMut = useMutation({
    mutationFn: ({ userId, roleId }: { userId: number; roleId: number }) =>
      assignRoleToUser(userId, roleId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); setSelectedRole('') },
  })

  const removeMut = useMutation({
    mutationFn: ({ userId, roleId }: { userId: number; roleId: number }) =>
      removeRoleFromUser(userId, roleId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })

  const assignedCodes = new Set(user.roles)
  const unassigned = roles.filter(r => !assignedCodes.has(r.code))

  return (
    <div className="px-12 py-3 bg-surface/50 border-t border-border/30">
      <p className="text-[10px] text-muted font-mono uppercase tracking-wider mb-2">Assigned Roles</p>
      <div className="flex flex-wrap gap-1.5 mb-3">
        {user.roles.length === 0 && <span className="text-xs text-muted/60 italic">No roles assigned</span>}
        {user.roles.map(code => {
          const role = roles.find(r => r.code === code)
          return (
            <RoleChip
              key={code}
              code={code}
              onRemove={role ? () => removeMut.mutate({ userId: user.id, roleId: role.id }) : undefined}
            />
          )
        })}
      </div>
      {unassigned.length > 0 && (
        <div className="flex items-center gap-2">
          <select
            value={selectedRole}
            onChange={e => setSelectedRole(e.target.value)}
            className="bg-surface border border-border rounded px-2 py-1 text-xs text-slate-200
                       focus:outline-none focus:border-accent/60"
          >
            <option value="">Add role…</option>
            {unassigned.map(r => <option key={r.id} value={r.id}>{r.code}</option>)}
          </select>
          <button
            disabled={!selectedRole || assignMut.isPending}
            onClick={() => selectedRole && assignMut.mutate({ userId: user.id, roleId: Number(selectedRole) })}
            className="flex items-center gap-1 px-2 py-1 bg-accent/20 hover:bg-accent/40 text-accent
                       text-xs rounded transition-colors disabled:opacity-40"
          >
            <ShieldPlus size={11} /> Assign
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

  const { data: users = [], isFetching } = useQuery({
    queryKey: ['users'],
    queryFn:  fetchUsers,
    refetchInterval: 30_000,
    enabled: isAdmin,
  })

  const { data: roles   = [] } = useQuery({ queryKey: ['roles'],   queryFn: fetchRoles })
  const { data: orgs    = [] } = useQuery({ queryKey: ['orgs'],    queryFn: fetchOrgs })
  const { data: circles = [] } = useQuery({ queryKey: ['circles'], queryFn: fetchCircles })
  const { data: bas     = [] } = useQuery({
    queryKey: ['bas', form.circle_id],
    queryFn:  () => fetchBAs(form.circle_id),
    enabled:  !!form.circle_id,
  })
  console.log(bas)

  const createMut = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      setShowForm(false)
      setForm(EMPTY)
      setError(null)
    },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed to create user'),
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

  if (!isAdmin) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 h-full">
        <Lock size={32} className="text-dim" />
        <p className="text-sm text-slate-300">SUPER_ADMIN role required</p>
        <p className="text-xs text-muted">Contact your administrator for access.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full p-4 gap-4 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold text-slate-100">Users</h1>
          <p className="text-xs text-muted mt-0.5">
            {users.length} accounts{isFetching && ' · refreshing...'}
          </p>
        </div>
        <button
          onClick={() => { setShowForm(s => !s); setError(null) }}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent/80
                     text-white text-sm font-medium rounded transition-colors"
        >
          {showForm ? <X size={13} /> : <Plus size={13} />}
          {showForm ? 'Cancel' : 'Add User'}
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form
          onSubmit={e => { e.preventDefault(); setError(null); createMut.mutate(form) }}
          className="bg-panel border border-border rounded p-4 grid grid-cols-3 gap-3 shrink-0
                     animate-[fade-in_0.2s_ease-out]"
        >
          <p className="col-span-3 text-sm font-medium text-slate-300">New user account</p>

          {[
            { label: 'Username *', field: 'username', type: 'text',     placeholder: 'john.doe', required: true },
            { label: 'Password *', field: 'password', type: 'password', placeholder: '••••••••', required: true },
            { label: 'Email',      field: 'email',    type: 'email',    placeholder: 'john@bsnl.in' },
            { label: 'Mobile',     field: 'mobile',   type: 'text',     placeholder: '+91 98765...' },
            { label: 'First Name', field: 'first_name', type: 'text',   placeholder: 'John' },
            { label: 'Last Name',  field: 'last_name',  type: 'text',   placeholder: 'Doe' },
          ].map(({ label, field, type, placeholder, required }) => (
            <div key={field}>
              <label className="block text-xs text-muted mb-1">{label}</label>
              <input className={inputCls} type={type} placeholder={placeholder} required={!!required}
                value={(form as any)[field] ?? ''}
                onChange={e => setForm(f => ({ ...f, [field]: e.target.value || undefined }))} />
            </div>
          ))}

          <div>
            <label className="block text-xs text-muted mb-1">User Type</label>
            <select className={inputCls} value={form.user_type ?? 'EMPLOYEE'}
              onChange={e => setForm(f => ({ ...f, user_type: e.target.value }))}>
              {USER_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Organization</label>
            <select className={inputCls} value={form.organization_id ?? ''}
              onChange={e => setForm(f => ({ ...f, organization_id: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">— None —</option>
              {orgs.map(o => <option key={o.id} value={o.id}>{o.code} — {o.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Circle</label>
            <select className={inputCls} value={form.circle_id ?? ''}
              onChange={e => setForm(f => ({ ...f, circle_id: e.target.value ? Number(e.target.value) : undefined, ba_id: undefined }))}>
              <option value="">— None —</option>
              {circles.map(c => <option key={c.id} value={c.id}>{c.cir_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">BA</label>
            <select className={inputCls} disabled={!form.circle_id} value={form.ba_id ?? ''}
              onChange={e => setForm(f => ({ ...f, ba_id: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">— Select circle first —</option>
              {bas.map(b => <option key={b.id} value={b.id}>{b.ba_name}</option>)}
            </select>
          </div>

          <div className="col-span-3 flex items-center justify-between">
            {error && <span className="text-xs text-alert">{error}</span>}
            <button type="submit" disabled={createMut.isPending}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent/80
                         text-white text-sm font-medium rounded transition-colors disabled:opacity-50">
              {createMut.isPending ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="flex-1 bg-panel border border-border rounded overflow-hidden flex flex-col min-h-0">
        {users.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <UsersIcon size={32} className="text-dim" />
            <p className="text-sm text-slate-300">No users found</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-panel border-b border-border z-10">
                <tr className="text-muted font-mono">
                  {['', 'Username', 'Email', 'Type', 'Roles', 'Status'].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <>
                    <tr key={user.id}
                      className="border-b border-border/50 hover:bg-border/20 transition-colors cursor-pointer"
                      onClick={() => toggleExpand(user.id)}>
                      <td className="px-4 py-3 w-8">
                        <ShieldPlus size={12} className={expanded.has(user.id) ? 'text-accent' : 'text-dim'} />
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-300">
                        {user.username}
                        {user.is_locked && <Lock size={10} className="inline ml-1.5 text-alert" />}
                      </td>
                      <td className="px-4 py-3 text-muted">{user.email ?? '—'}</td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-[10px] bg-accent/10 text-accent px-1.5 rounded">
                          {user.user_type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {user.roles.slice(0, 3).map(r => <RoleChip key={r} code={r} />)}
                          {user.roles.length > 3 && (
                            <span className="text-muted text-[10px]">+{user.roles.length - 3}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`size-1.5 rounded-full inline-block ${user.is_active ? 'bg-online' : 'bg-dim'}`} />
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
