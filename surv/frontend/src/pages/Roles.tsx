import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, X, Lock, Shield } from 'lucide-react'
import {
  fetchRoles, fetchPermissions, fetchRolePermissions,
  createRole, createPermission,
  assignPermissionToRole, removePermissionFromRole,
  type Role, type Permission,
} from '../api/client'
import { hasPermission, hasRole } from '../lib/auth'

const PERM_GROUP_COLORS: Record<string, { bg: string, color: string }> = {
  camera:   { bg: 'oklch(0.55 0.15 250 / 0.1)', color: 'oklch(0.55 0.15 250)' },
  user:     { bg: 'oklch(0.72 0.17 150 / 0.1)', color: 'var(--color-success)' },
  customer: { bg: 'oklch(0.65 0.18 290 / 0.1)', color: 'oklch(0.65 0.18 290)' },
  report:   { bg: 'oklch(0.78 0.15 75 / 0.1)', color: 'var(--color-warning)' },
  system:   { bg: 'oklch(0.62 0.22 25 / 0.1)', color: 'var(--color-destructive)' },
}

function permColor(code: string) {
  const prefix = code.split('.')[0]
  return PERM_GROUP_COLORS[prefix] ?? { bg: 'oklch(0.3 0.02 260 / 0.2)', color: 'var(--color-muted-foreground)' }
}

function groupPerms(perms: Permission[]): Record<string, Permission[]> {
  const groups: Record<string, Permission[]> = {}
  for (const p of perms) {
    const grp = p.code.split('.')[0]
    if (!groups[grp]) groups[grp] = []
    groups[grp].push(p)
  }
  return groups
}

const inputStyle = {
  background: 'oklch(0.28 0.03 260 / 0.5)',
  color: 'var(--color-foreground)',
  boxShadow: '0 0 0 1px var(--color-border)',
} as React.CSSProperties

export default function Roles() {
  const qc = useQueryClient()
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null)
  const [showRoleForm, setShowRoleForm]   = useState(false)
  const [showPermForm, setShowPermForm]   = useState(false)
  const [roleForm, setRoleForm]           = useState({ code: '', name: '', description: '' })
  const [permForm, setPermForm]           = useState({ code: '', name: '' })
  const [error, setError]                 = useState<string | null>(null)

  const canEdit = hasPermission('system.settings') || hasRole('SUPER_ADMIN')

  const { data: roles = [] }       = useQuery({ queryKey: ['roles'],       queryFn: fetchRoles })
  const { data: allPerms = [] }    = useQuery({ queryKey: ['permissions'], queryFn: fetchPermissions })
  const { data: rolePerms = [] }   = useQuery({
    queryKey: ['role-perms', selectedRoleId],
    queryFn:  () => fetchRolePermissions(selectedRoleId!),
    enabled:  selectedRoleId != null,
  })

  const createRoleMut = useMutation({
    mutationFn: createRole,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['roles'] }); setShowRoleForm(false); setRoleForm({ code:'', name:'', description:'' }); setError(null) },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed'),
  })
  const createPermMut = useMutation({
    mutationFn: createPermission,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['permissions'] }); setShowPermForm(false); setPermForm({ code:'', name:'' }); setError(null) },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed'),
  })

  const assignMut = useMutation({
    mutationFn: ({ roleId, permId }: { roleId: number; permId: number }) => assignPermissionToRole(roleId, permId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['role-perms', selectedRoleId] }),
  })
  const removeMut = useMutation({
    mutationFn: ({ roleId, permId }: { roleId: number; permId: number }) => removePermissionFromRole(roleId, permId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['role-perms', selectedRoleId] }),
  })

  const rolePermIds = new Set(rolePerms.map((p: Permission) => p.id))
  const selectedRole = roles.find((r: Role) => r.id === selectedRoleId)
  const groupedPerms = groupPerms(allPerms)

  const inputCls = "w-full rounded-md px-3 py-1.5 text-xs outline-none transition-all disabled:opacity-50"

  if (!canEdit) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 h-full animate-[fade-in_0.2s_ease-out]">
        <Lock size={32} style={{ color: 'var(--color-dim)' }} />
        <p className="text-sm" style={{ color: 'var(--color-foreground)' }}>system.settings permission required</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full p-4 lg:p-6 gap-5 animate-[fade-in_0.2s_ease-out]">
      <div className="shrink-0">
        <h1 className="text-base font-semibold flex items-center gap-2" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
          <Shield size={16} style={{ color: 'var(--color-primary)' }} /> Roles & Permissions
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
          {roles.length} roles · {allPerms.length} permissions
        </p>
      </div>

      <div className="flex-1 flex gap-5 min-h-0">
        {/* Left: Roles panel */}
        <div className="w-72 flex flex-col gap-3 shrink-0">
          <div className="flex items-center justify-between">
            <p className="text-[10px] uppercase tracking-widest font-semibold" style={{ color: 'var(--color-muted-foreground)' }}>Roles</p>
            <button onClick={() => setShowRoleForm(s => !s)}
                    className="flex items-center gap-1 text-xs font-medium transition-colors"
                    style={{ color: 'var(--color-primary)' }}
                    onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.78 0.14 200 / 0.1)')}
                    onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
                    >
              {showRoleForm ? <X size={11} /> : <Plus size={11} />}
              {showRoleForm ? 'Cancel' : 'New role'}
            </button>
          </div>

          {showRoleForm && (
            <form onSubmit={e => { e.preventDefault(); setError(null); createRoleMut.mutate(roleForm) }}
                  className="p-4 rounded-xl flex flex-col gap-3 animate-[fade-in_0.15s_ease-out]"
                  style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
              <input className={inputCls} style={inputStyle} required placeholder="Role code (e.g. SITE_ADMIN)"
                     value={roleForm.code} onChange={e => setRoleForm(f => ({ ...f, code: e.target.value }))} />
              <input className={inputCls} style={inputStyle} placeholder="Display name"
                     value={roleForm.name} onChange={e => setRoleForm(f => ({ ...f, name: e.target.value }))} />
              {error && <p className="text-xs" style={{ color: 'var(--color-destructive)' }}>{error}</p>}
              <button type="submit" disabled={createRoleMut.isPending}
                      className="px-3 py-1.5 rounded-md text-xs font-medium transition-all disabled:opacity-50 mt-1"
                      style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
                {createRoleMut.isPending ? 'Creating...' : 'Create Role'}
              </button>
            </form>
          )}

          <div className="flex-1 rounded-xl overflow-y-auto"
               style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
            {roles.map((role: Role) => {
              const isSelected = selectedRoleId === role.id
              return (
                <button
                  key={role.id}
                  onClick={() => setSelectedRoleId(isSelected ? null : role.id)}
                  className="w-full text-left px-4 py-3 transition-colors"
                  style={{
                    borderBottom: '1px solid var(--color-border)',
                    background: isSelected ? 'oklch(0.78 0.14 200 / 0.1)' : 'transparent',
                  }}
                  onMouseOver={e => { if (!isSelected) e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)' }}
                  onMouseOut={e => { if (!isSelected) e.currentTarget.style.background = 'transparent' }}
                >
                  <p className="font-mono text-xs font-medium" style={{ color: isSelected ? 'var(--color-primary)' : 'var(--color-foreground)' }}>
                    {role.code}
                  </p>
                  {role.name && <p className="text-[10px] mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>{role.name}</p>}
                </button>
              )
            })}
            {roles.length === 0 && <p className="px-4 py-5 text-xs italic" style={{ color: 'var(--color-dim)' }}>No roles defined</p>}
          </div>
        </div>

        {/* Right: Permissions matrix */}
        <div className="flex-1 flex flex-col gap-3 min-w-0">
          <div className="flex items-center justify-between">
            <p className="text-[10px] uppercase tracking-widest font-semibold" style={{ color: 'var(--color-muted-foreground)' }}>
              {selectedRole ? `Permissions — ${selectedRole.code}` : 'All Permissions (select a role to assign)'}
            </p>
            <button onClick={() => setShowPermForm(s => !s)}
                    className="flex items-center gap-1 text-xs font-medium transition-colors"
                    style={{ color: 'var(--color-primary)' }}
                    onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.78 0.14 200 / 0.1)')}
                    onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
                    >
              {showPermForm ? <X size={11} /> : <Plus size={11} />}
              {showPermForm ? 'Cancel' : 'New permission'}
            </button>
          </div>

          {showPermForm && (
            <form onSubmit={e => { e.preventDefault(); setError(null); createPermMut.mutate(permForm) }}
                  className="flex gap-3 animate-[fade-in_0.15s_ease-out]">
              <input className={`flex-1 ${inputCls}`} style={inputStyle} required placeholder="camera.snapshot"
                     value={permForm.code} onChange={e => setPermForm(f => ({ ...f, code: e.target.value }))} />
              <input className={`flex-1 ${inputCls}`} style={inputStyle} placeholder="Display name"
                     value={permForm.name} onChange={e => setPermForm(f => ({ ...f, name: e.target.value }))} />
              <button type="submit" disabled={createPermMut.isPending}
                      className="px-4 py-1.5 rounded-md text-xs font-medium transition-all disabled:opacity-50"
                      style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
                {createPermMut.isPending ? '...' : 'Create'}
              </button>
            </form>
          )}

          <div className="flex-1 rounded-xl overflow-y-auto p-5"
               style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
            {Object.entries(groupedPerms).map(([group, perms]) => (
              <div key={group} className="mb-6">
                <p className="font-mono text-[10px] uppercase tracking-widest mb-3" style={{ color: 'var(--color-muted-foreground)' }}>{group}</p>
                <div className="flex flex-wrap gap-2.5">
                  {perms.map((perm: Permission) => {
                    const assigned = selectedRoleId != null && rolePermIds.has(perm.id)
                    const tone = permColor(perm.code)
                    return (
                      <button
                        key={perm.id}
                        disabled={selectedRoleId == null}
                        onClick={() => {
                          if (!selectedRoleId) return
                          if (assigned) removeMut.mutate({ roleId: selectedRoleId, permId: perm.id })
                          else assignMut.mutate({ roleId: selectedRoleId, permId: perm.id })
                        }}
                        className="font-mono text-[10px] px-2.5 py-1 rounded-md transition-all disabled:cursor-not-allowed"
                        style={assigned
                          ? { background: tone.bg, color: tone.color, boxShadow: `0 0 0 1px ${tone.color}` }
                          : { background: 'transparent', color: 'var(--color-muted-foreground)', boxShadow: '0 0 0 1px var(--color-border)' }
                        }
                        onMouseOver={e => { if (!assigned && selectedRoleId) e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)' }}
                        onMouseOut={e => { if (!assigned) e.currentTarget.style.background = 'transparent' }}
                      >
                        {perm.code}
                        {assigned && ' ✓'}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
            {allPerms.length === 0 && <p className="text-xs italic" style={{ color: 'var(--color-dim)' }}>No permissions defined</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
