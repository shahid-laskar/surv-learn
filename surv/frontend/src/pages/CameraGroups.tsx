import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layers, Plus, X, Camera, ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import {
  fetchCameraGroups, createCameraGroup, addCameraToGroup,
  fetchCameras,
  type CameraGroup, type CameraGroupCreate,
} from '../api/client'
import { hasPermission, hasRole } from '../lib/auth'

const EMPTY: CameraGroupCreate = { name: '' }

const inputStyle = {
  background: 'oklch(0.28 0.03 260 / 0.5)',
  color: 'var(--color-foreground)',
  boxShadow: '0 0 0 1px var(--color-border)',
} as React.CSSProperties

function GroupCamerasPanel({ group, cameras }: { group: CameraGroup; cameras: ReturnType<typeof fetchCameras> extends Promise<infer T> ? T : never }) {
  const qc = useQueryClient()
  const [selectedCam, setSelectedCam] = useState('')
  const canEdit = hasPermission('camera.update') || hasRole('SUPER_ADMIN')

  const addMut = useMutation({
    mutationFn: (cameraId: number) => addCameraToGroup(group.id, cameraId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cameras'] }); setSelectedCam('') },
  })

  return (
    <div className="px-12 py-4" style={{ background: 'oklch(0.2 0.035 260 / 0.5)', borderTop: '1px solid var(--color-border)' }}>
      <p className="text-[10px] uppercase tracking-widest font-semibold mb-3" style={{ color: 'var(--color-muted-foreground)' }}>Cameras</p>
      
      {canEdit && (
        <div className="flex items-center gap-2 mb-3 max-w-md">
          <select value={selectedCam} onChange={e => setSelectedCam(e.target.value)}
                  className="flex-1 rounded-md px-3 py-1.5 text-xs outline-none" style={inputStyle}>
            <option value="">Add camera to group…</option>
            {cameras.map(c => <option key={c.cam_id} value={c.id}>{c.cam_id}{c.cam_name ? ` — ${c.cam_name}` : ''}</option>)}
          </select>
          <button disabled={!selectedCam || addMut.isPending}
                  onClick={() => selectedCam && addMut.mutate(Number(selectedCam))}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all disabled:opacity-50"
                  style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
            {addMut.isPending ? <Loader2 size={11} className="animate-spin" /> : <Plus size={11} />} Add
          </button>
        </div>
      )}
      <p className="text-xs italic" style={{ color: 'var(--color-dim)' }}>
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

  const { data: groups  = [], isFetching } = useQuery({ queryKey: ['camera-groups'], queryFn: fetchCameraGroups, refetchInterval: 30_000 })
  const { data: cameras = [] } = useQuery({ queryKey: ['cameras'], queryFn: fetchCameras })

  const createMut = useMutation({
    mutationFn: createCameraGroup,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['camera-groups'] }); setShowForm(false); setForm(EMPTY); setError(null) },
    onError: (e: any) => setError(e.response?.data?.detail ?? 'Failed to create group'),
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
            <Layers size={16} style={{ color: 'var(--color-primary)' }} /> Camera Groups
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
            {groups.length} groups{isFetching && ' · refreshing...'}
          </p>
        </div>
        {canEdit && (
          <button onClick={() => { setShowForm(s => !s); setError(null) }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
                  style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
            {showForm ? <X size={13} /> : <Plus size={13} />}
            {showForm ? 'Cancel' : 'New Group'}
          </button>
        )}
      </div>

      {/* Create form */}
      {showForm && (
        <form onSubmit={e => { e.preventDefault(); setError(null); createMut.mutate(form) }}
              className="rounded-2xl p-5 flex items-end gap-4 shrink-0 animate-[fade-in_0.2s_ease-out]"
              style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
          <div className="flex-1">
            <label className="block text-[10px] font-medium mb-1.5 uppercase tracking-widest" style={{ color: 'var(--color-muted-foreground)' }}>Group name *</label>
            <input className={inputCls} style={inputStyle} required placeholder="Kerala Circle CCTV"
                   value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>
          {error && <span className="text-xs" style={{ color: 'var(--color-destructive)' }}>{error}</span>}
          <button type="submit" disabled={createMut.isPending}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-all disabled:opacity-50"
                  style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}>
            {createMut.isPending ? 'Saving...' : 'Create'}
          </button>
        </form>
      )}

      {/* Groups table */}
      <div className="flex-1 rounded-2xl overflow-hidden flex flex-col min-h-0"
           style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
        {groups.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <Layers size={32} style={{ color: 'var(--color-dim)' }} />
            <p className="text-sm" style={{ color: 'var(--color-foreground)' }}>No camera groups yet</p>
            {canEdit && <p className="text-xs" style={{ color: 'var(--color-muted-foreground)' }}>Create a group to organize cameras</p>}
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="text-[11px] font-medium uppercase tracking-widest sticky top-0"
                    style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)', background: 'oklch(0.22 0.035 260)' }}>
                  {['', 'Group Name', 'Org ID', 'Customer ID'].map(h => <th key={h} className="px-4 py-3 text-left">{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {groups.map((group: CameraGroup) => (
                  <>
                    <tr key={group.id}
                        className="cursor-pointer transition-colors last:border-b-0"
                        style={{ borderBottom: '1px solid var(--color-border)' }}
                        onClick={() => toggleExpand(group.id)}
                        onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)')}
                        onMouseOut={e => (e.currentTarget.style.background = 'transparent')}>
                      <td className="px-4 py-3 w-8">
                        {expanded.has(group.id)
                          ? <ChevronDown size={14} style={{ color: 'var(--color-muted-foreground)' }} />
                          : <ChevronRight size={14} style={{ color: 'var(--color-muted-foreground)' }} />}
                      </td>
                      <td className="px-4 py-3 font-medium flex items-center gap-2" style={{ color: 'var(--color-foreground)' }}>
                        <Camera size={13} style={{ color: 'var(--color-muted-foreground)' }} />
                        {group.name}
                      </td>
                      <td className="px-4 py-3 font-mono" style={{ color: 'var(--color-muted-foreground)' }}>{group.organization_id ?? '—'}</td>
                      <td className="px-4 py-3 font-mono" style={{ color: 'var(--color-muted-foreground)' }}>{group.customer_id ?? '—'}</td>
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
