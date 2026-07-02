import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, X, Lock } from 'lucide-react'
import {
  fetchRoles, fetchPermissions, fetchRolePermissions,
  createRole, createPermission,
  assignPermissionToRole, removePermissionFromRole,
  type Role, type Permission,
} from '../api/client'
import { hasPermission, hasRole } from '../lib/auth'

const PERM_GROUP_COLORS: Record<string, string> = {
  camera:  'bg-blue-500/10 text-blue-300 border-blue-500/20',
  user:    'bg-green-500/10 text-green-300 border-green-500/20',
  customer:'bg-purple-500/10 text-purple-300 border-purple-500/20',
  report:  'bg-yellow-500/10 text-yellow-300 border-yellow-500/20',
  system:  'bg-red-500/10 text-red-300 border-red-500/20',
}

function permColor(code: string) {
  const prefix = code.split('.')[0]
  return PERM_GROUP_COLORS[prefix] ?? 'bg-dim/10 text-muted border-dim'
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
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['roles'] }); setShowRoleForm(false); setRoleForm({ code:'', name:'', description:'' }) },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed'),
  })
  const createPermMut = useMutation({
    mutationFn: createPermission,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['permissions'] }); setShowPermForm(false); setPermForm({ code:'', name:'' }) },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed'),
  })

  const assignMut = useMutation({
    mutationFn: ({ roleId, permId }: { roleId: number; permId: number }) =>
      assignPermissionToRole(roleId, permId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['role-perms', selectedRoleId] }),
  })
  const removeMut = useMutation({
    mutationFn: ({ roleId, permId }: { roleId: number; permId: number }) =>
      removePermissionFromRole(roleId, permId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['role-perms', selectedRoleId] }),
  })

  const rolePermIds = new Set(rolePerms.map((p: Permission) => p.id))
  const selectedRole = roles.find((r: Role) => r.id === selectedRoleId)
  const groupedPerms = groupPerms(allPerms)

  const inputCls = `w-full bg-surface border border-border rounded px-3 py-2 text-sm
                    text-slate-200 placeholder-muted focus:outline-none focus:border-accent/60 transition-colors`

  if (!canEdit) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 h-full">
        <Lock size={32} className="text-dim" />
        <p className="text-sm text-slate-300">system.settings permission required</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full p-4 gap-4 animate-[fade-in_0.2s_ease-out]">
      <div className="shrink-0">
        <h1 className="text-base font-semibold text-slate-100">Roles & Permissions</h1>
        <p className="text-xs text-muted mt-0.5">{roles.length} roles · {allPerms.length} permissions</p>
      </div>

      <div className="flex-1 flex gap-4 min-h-0">
        {/* Left: Roles panel */}
        <div className="w-64 flex flex-col gap-3 shrink-0">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted font-mono uppercase tracking-wider">Roles</p>
            <button onClick={() => setShowRoleForm(s => !s)}
              className="flex items-center gap-1 text-xs text-accent hover:text-accent/70 transition-colors">
              {showRoleForm ? <X size={11} /> : <Plus size={11} />}
              {showRoleForm ? 'Cancel' : 'New role'}
            </button>
          </div>

          {showRoleForm && (
            <form onSubmit={e => { e.preventDefault(); setError(null); createRoleMut.mutate(roleForm) }}
              className="bg-panel border border-border rounded p-3 flex flex-col gap-2 animate-[fade-in_0.15s_ease-out]">
              <input className={inputCls} required placeholder="Role code (e.g. SITE_ADMIN)"
                value={roleForm.code} onChange={e => setRoleForm(f => ({ ...f, code: e.target.value }))} />
              <input className={inputCls} placeholder="Display name"
                value={roleForm.name} onChange={e => setRoleForm(f => ({ ...f, name: e.target.value }))} />
              {error && <p className="text-xs text-alert">{error}</p>}
              <button type="submit" disabled={createRoleMut.isPending}
                className="px-2 py-1.5 bg-accent/80 hover:bg-accent text-white text-xs rounded transition-colors disabled:opacity-50">
                {createRoleMut.isPending ? 'Creating...' : 'Create Role'}
              </button>
            </form>
          )}

          <div className="flex-1 bg-panel border border-border rounded overflow-y-auto">
            {roles.map((role: Role) => (
              <button
                key={role.id}
                onClick={() => setSelectedRoleId(role.id === selectedRoleId ? null : role.id)}
                className={`w-full text-left px-3 py-2.5 border-b border-border/50 transition-colors
                            ${selectedRoleId === role.id
                              ? 'bg-accent/10 text-accent'
                              : 'text-muted hover:bg-border/40 hover:text-slate-200'
                            }`}
              >
                <p className="font-mono text-xs">{role.code}</p>
                {role.name && <p className="text-[10px] opacity-70 mt-0.5">{role.name}</p>}
              </button>
            ))}
            {roles.length === 0 && <p className="px-3 py-4 text-xs text-muted/60 italic">No roles defined</p>}
          </div>
        </div>

        {/* Right: Permissions matrix */}
        <div className="flex-1 flex flex-col gap-3 min-w-0">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted font-mono uppercase tracking-wider">
              {selectedRole ? `Permissions — ${selectedRole.code}` : 'All Permissions (select a role to assign)'}
            </p>
            <button onClick={() => setShowPermForm(s => !s)}
              className="flex items-center gap-1 text-xs text-accent hover:text-accent/70 transition-colors">
              {showPermForm ? <X size={11} /> : <Plus size={11} />}
              {showPermForm ? 'Cancel' : 'New permission'}
            </button>
          </div>

          {showPermForm && (
            <form onSubmit={e => { e.preventDefault(); setError(null); createPermMut.mutate(permForm) }}
              className="flex gap-2 animate-[fade-in_0.15s_ease-out]">
              <input className={`flex-1 ${inputCls}`} required placeholder="camera.snapshot"
                value={permForm.code} onChange={e => setPermForm(f => ({ ...f, code: e.target.value }))} />
              <input className={`flex-1 ${inputCls}`} placeholder="Display name"
                value={permForm.name} onChange={e => setPermForm(f => ({ ...f, name: e.target.value }))} />
              <button type="submit" disabled={createPermMut.isPending}
                className="px-3 py-2 bg-accent/80 hover:bg-accent text-white text-xs rounded transition-colors whitespace-nowrap disabled:opacity-50">
                {createPermMut.isPending ? '...' : 'Create'}
              </button>
            </form>
          )}

          <div className="flex-1 bg-panel border border-border rounded overflow-y-auto p-4">
            {Object.entries(groupedPerms).map(([group, perms]) => (
              <div key={group} className="mb-5">
                <p className="font-mono text-[10px] text-muted uppercase tracking-widest mb-2">{group}</p>
                <div className="flex flex-wrap gap-2">
                  {perms.map((perm: Permission) => {
                    const assigned = selectedRoleId != null && rolePermIds.has(perm.id)
                    return (
                      <button
                        key={perm.id}
                        disabled={selectedRoleId == null}
                        onClick={() => {
                          if (!selectedRoleId) return
                          if (assigned) {
                            removeMut.mutate({ roleId: selectedRoleId, permId: perm.id })
                          } else {
                            assignMut.mutate({ roleId: selectedRoleId, permId: perm.id })
                          }
                        }}
                        className={`font-mono text-[10px] px-2.5 py-1 rounded border transition-all
                                    ${assigned
                                      ? `${permColor(perm.code)} ring-1 ring-current`
                                      : 'bg-dim/10 text-dim border-dim/30 hover:text-muted hover:border-border'
                                    }
                                    disabled:cursor-default`}
                      >
                        {perm.code}
                        {assigned && ' ✓'}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
            {allPerms.length === 0 && <p className="text-xs text-muted/60 italic">No permissions defined</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
