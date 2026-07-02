import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layers, Plus, X, Camera, ChevronDown, ChevronRight } from 'lucide-react'
import {
  fetchCameraGroups, createCameraGroup, addCameraToGroup, removeCameraFromGroup,
  fetchCameras,
  type CameraGroup, type CameraGroupCreate,
} from '../api/client'
import { hasPermission, hasRole } from '../lib/auth'

const EMPTY: CameraGroupCreate = { name: '' }

function GroupCamerasPanel({ group, cameras }: { group: CameraGroup; cameras: ReturnType<typeof fetchCameras> extends Promise<infer T> ? T : never }) {
  const qc = useQueryClient()
  const [selectedCam, setSelectedCam] = useState('')
  const canEdit = hasPermission('camera.update') || hasRole('SUPER_ADMIN')

  // We derive which cameras are "in group" by filtering cameras whose group assignment we know.
  // Since the backend doesn't directly expose group→cameras via a list endpoint,
  // we use a simple camera picker and track removals optimistically.
  const addMut = useMutation({
    mutationFn: (cameraId: number) => addCameraToGroup(group.id, cameraId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cameras'] }); setSelectedCam('') },
  })
  const removeMut = useMutation({
    mutationFn: (cameraId: number) => removeCameraFromGroup(group.id, cameraId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cameras'] }),
  })
  console.log(removeMut)

  return (
    <div className="px-12 py-3 bg-surface/50 border-t border-border/30">
      <p className="text-[10px] text-muted font-mono uppercase tracking-wider mb-2">Cameras</p>

      {canEdit && (
        <div className="flex items-center gap-2 mb-3">
          <select value={selectedCam} onChange={e => setSelectedCam(e.target.value)}
            className="bg-surface border border-border rounded px-2 py-1 text-xs text-slate-200
                       focus:outline-none focus:border-accent/60 flex-1">
            <option value="">Add camera to group…</option>
            {cameras.map(c => <option key={c.cam_id} value={c.id}>{c.cam_id}{c.cam_name ? ` — ${c.cam_name}` : ''}</option>)}
          </select>
          <button
            disabled={!selectedCam || addMut.isPending}
            onClick={() => selectedCam && addMut.mutate(Number(selectedCam))}
            className="flex items-center gap-1 px-2.5 py-1 bg-accent/20 hover:bg-accent/40 text-accent
                       text-xs rounded transition-colors disabled:opacity-40"
          >
            <Plus size={11} /> Add
          </button>
        </div>
      )}
      <p className="text-xs text-muted/60 italic">
        (Use the add picker above to assign cameras. Camera-to-group mapping is write-only in this view.)
      </p>
    </div>
  )
}

export default function CameraGroups() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm]         = useState<CameraGroupCreate>(EMPTY)
  const [error, setError]       = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  const canEdit = hasPermission('camera.update') || hasRole('SUPER_ADMIN')

  const { data: groups  = [], isFetching } = useQuery({
    queryKey:        ['camera-groups'],
    queryFn:         fetchCameraGroups,
    refetchInterval: 30_000,
  })
  const { data: cameras = [] } = useQuery({ queryKey: ['cameras'], queryFn: fetchCameras })

  const createMut = useMutation({
    mutationFn: createCameraGroup,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['camera-groups'] })
      setShowForm(false)
      setForm(EMPTY)
      setError(null)
    },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed to create group'),
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
          <h1 className="text-base font-semibold text-slate-100">Camera Groups</h1>
          <p className="text-xs text-muted mt-0.5">
            {groups.length} groups{isFetching && ' · refreshing...'}
          </p>
        </div>
        {canEdit && (
          <button
            onClick={() => { setShowForm(s => !s); setError(null) }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent/80
                       text-white text-sm font-medium rounded transition-colors"
          >
            {showForm ? <X size={13} /> : <Plus size={13} />}
            {showForm ? 'Cancel' : 'New Group'}
          </button>
        )}
      </div>

      {/* Create form */}
      {showForm && (
        <form
          onSubmit={e => { e.preventDefault(); setError(null); createMut.mutate(form) }}
          className="bg-panel border border-border rounded p-4 flex items-end gap-3 shrink-0
                     animate-[fade-in_0.2s_ease-out]"
        >
          <div className="flex-1">
            <label className="block text-xs text-muted mb-1">Group name *</label>
            <input className={inputCls} required placeholder="Kerala Circle CCTV"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>
          {error && <span className="text-xs text-alert">{error}</span>}
          <button type="submit" disabled={createMut.isPending}
            className="flex items-center gap-1.5 px-3 py-2 bg-accent hover:bg-accent/80
                       text-white text-sm font-medium rounded transition-colors disabled:opacity-50">
            {createMut.isPending ? 'Saving...' : 'Create'}
          </button>
        </form>
      )}

      {/* Groups table */}
      <div className="flex-1 bg-panel border border-border rounded overflow-hidden flex flex-col min-h-0">
        {groups.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <Layers size={32} className="text-dim" />
            <p className="text-sm text-slate-300">No camera groups yet</p>
            {canEdit && <p className="text-xs text-muted">Create a group to organize cameras</p>}
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-panel border-b border-border z-10">
                <tr className="text-muted font-mono">
                  {['', 'Group Name', 'Org ID', 'Customer ID'].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {groups.map((group: CameraGroup) => (
                  <>
                    <tr key={group.id}
                      className="border-b border-border/50 hover:bg-border/20 transition-colors cursor-pointer"
                      onClick={() => toggleExpand(group.id)}>
                      <td className="px-4 py-3 w-8">
                        {expanded.has(group.id)
                          ? <ChevronDown size={12} className="text-muted" />
                          : <ChevronRight size={12} className="text-muted" />
                        }
                      </td>
                      <td className="px-4 py-3 text-slate-200 font-medium flex items-center gap-2">
                        <Camera size={13} className="text-muted shrink-0" />
                        {group.name}
                      </td>
                      <td className="px-4 py-3 font-mono text-muted">{group.organization_id ?? '—'}</td>
                      <td className="px-4 py-3 font-mono text-muted">{group.customer_id ?? '—'}</td>
                    </tr>
                    {expanded.has(group.id) && (
                      <tr key={`cams-${group.id}`}>
                        <td colSpan={4} className="p-0">
                          <GroupCamerasPanel group={group} cameras={cameras} />
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
