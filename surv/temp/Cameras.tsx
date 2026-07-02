import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { Plus, Trash2, X, Check, Wifi } from 'lucide-react'
import { fetchCameras, createCamera, updateCamera, deleteCamera, type CameraCreate } from '../api/client'
import StatusBadge from '../components/StatusBadge'

const EMPTY: CameraCreate = {
  cam_id: '', cam_name: '', cam_ip: '',
  cam_port: 554, onvif_port: 80,
  onvif_username: 'admin', onvif_password: 'admin',
  motion_active: true,
}

const FIELDS: {
  label: string; field: keyof CameraCreate
  type: string; placeholder: string; required?: boolean
}[] = [
  { label: 'Camera ID',  field: 'cam_id',        type: 'text',     placeholder: 'CAMKRTVM00001', required: true },
  { label: 'Name',       field: 'cam_name',       type: 'text',     placeholder: 'Main Entrance' },
  { label: 'IP Address', field: 'cam_ip',         type: 'text',     placeholder: '192.168.1.100', required: true },
  { label: 'RTSP Port',  field: 'cam_port',       type: 'number',   placeholder: '554' },
  { label: 'ONVIF Port', field: 'onvif_port',     type: 'number',   placeholder: '80' },
  { label: 'RTSP URL',   field: 'rtsp_url',       type: 'text',     placeholder: 'rtsp://... (optional)' },
  { label: 'Username',   field: 'onvif_username', type: 'text',     placeholder: 'admin' },
  { label: 'Password',   field: 'onvif_password', type: 'password', placeholder: '••••••' },
]

export default function Cameras() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm]         = useState<CameraCreate>(EMPTY)
  const [error, setError]       = useState<string | null>(null)

  const invalidate = () => qc.invalidateQueries({ queryKey: ['cameras'] })

  const { data: cameras = [], isFetching } = useQuery({
    queryKey:       ['cameras'],
    queryFn:        fetchCameras,
    refetchInterval: 15_000,
  })

  const createMut = useMutation({
    mutationFn: createCamera,
    onSuccess:  () => { invalidate(); setShowForm(false); setForm(EMPTY); setError(null) },
    onError:    (e: Error | unknown) => setError((e as {response?: {data?: {detail?: string}}}).response?.data?.detail ?? 'Failed to create camera'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof updateCamera>[1] }) =>
      updateCamera(id, data),
    onSuccess: invalidate,
  })

  const deleteMut = useMutation({ mutationFn: deleteCamera, onSuccess: invalidate })

  function set(field: keyof CameraCreate, value: string | number | boolean) {
    setForm(f => ({ ...f, [field]: value }))
  }

  const inputCls = `w-full bg-surface border border-border rounded px-3 py-2 text-sm
                    text-slate-200 placeholder-muted focus:outline-none
                    focus:border-accent/60 transition-colors`

  return (
    <div className="flex flex-col h-full p-4 gap-4 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold text-slate-100">Cameras</h1>
          <p className="text-xs text-muted mt-0.5">
            {cameras.length} registered · {cameras.filter(c => c.is_online).length} online
            {isFetching && ' · refreshing...'}
          </p>
        </div>
        <button
          onClick={() => { setShowForm(s => !s); setError(null) }}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent/80
                     text-white text-sm font-medium rounded transition-colors"
        >
          {showForm ? <X size={13} /> : <Plus size={13} />}
          {showForm ? 'Cancel' : 'Add camera'}
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <form
          onSubmit={e => { e.preventDefault(); setError(null); createMut.mutate(form) }}
          className="bg-panel border border-border rounded p-4 grid grid-cols-2 gap-3 shrink-0
                     animate-[fade-in_0.2s_ease-out]"
        >
          <p className="col-span-2 text-sm font-medium text-slate-300">Register new camera</p>

          {FIELDS.map(({ label, field, type, placeholder, required }) => (
            <div key={field}>
              <label className="block text-xs text-muted mb-1">{label}</label>
              <input
                type={type}
                placeholder={placeholder}
                required={required}
                value={String(form[field as keyof CameraCreate] ?? '')}
                onChange={e => set(field, type === 'number' ? parseInt(e.target.value) || 0 : e.target.value)}
                className={inputCls}
              />
            </div>
          ))}

          <div className="col-span-2 flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={!!form.motion_active}
                onChange={e => set('motion_active', e.target.checked)}
                className="accent-accent"
              />
              <span className="text-xs text-slate-300">Enable motion detection</span>
            </label>
            <div className="flex items-center gap-2">
              {error && <span className="text-xs text-alert">{error}</span>}
              <button
                type="submit"
                disabled={createMut.isPending}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accent/80
                           text-white text-sm font-medium rounded transition-colors disabled:opacity-50"
              >
                <Check size={13} />
                {createMut.isPending ? 'Saving...' : 'Save camera'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="flex-1 bg-panel border border-border rounded overflow-hidden flex flex-col min-h-0">
        {cameras.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <Wifi size={32} className="text-dim" />
            <p className="text-sm text-slate-300">No cameras yet</p>
            <p className="text-xs text-muted">Add a camera to start recording</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-panel border-b border-border z-10">
                <tr className="text-muted font-mono">
                  {['Status', 'Camera ID', 'Name', 'IP', 'Motion', 'Last Seen', ''].map(h => (
                    <th key={h} className={`px-4 py-2.5 ${h === '' ? 'text-right' : 'text-left'}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cameras.map(cam => (
                  <tr key={cam.cam_id} className="border-b border-border/50 hover:bg-border/30 transition-colors">
                    <td className="px-4 py-3"><StatusBadge online={cam.is_online} /></td>
                    <td className="px-4 py-3 font-mono text-slate-300">{cam.cam_id}</td>
                    <td className="px-4 py-3 text-muted">{cam.cam_name ?? <span className="text-dim italic">—</span>}</td>
                    <td className="px-4 py-3 font-mono text-muted">{cam.cam_ip}:{cam.cam_port}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => updateMut.mutate({ id: cam.cam_id, data: { motion_active: !cam.motion_active } })}
                        className={`font-mono text-[10px] px-2 py-0.5 rounded border transition-colors
                                    ${cam.motion_active
                                      ? 'border-online/40 text-online hover:bg-online/10'
                                      : 'border-dim text-muted hover:bg-border'}`}
                      >
                        {cam.motion_active ? 'ON' : 'OFF'}
                      </button>
                    </td>
                    <td className="px-4 py-3 font-mono text-muted">
                      {cam.last_seen ? format(new Date(cam.last_seen), 'dd MMM HH:mm:ss') : <span className="text-dim">Never</span>}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => { if (confirm(`Remove ${cam.cam_id}?`)) deleteMut.mutate(cam.cam_id) }}
                        className="text-muted hover:text-alert transition-colors"
                        title="Deactivate"
                      >
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
