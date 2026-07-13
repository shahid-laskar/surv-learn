import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { Plus, Trash2, X, Check, Wifi, Edit2, Loader2 } from 'lucide-react'
import { fetchCameras, createCamera, updateCamera, deleteCamera, fetchOrgs, fetchCustomers, type CameraCreate } from '../api/client'

const EMPTY: CameraCreate = {
  cam_id: '', cam_name: '', cam_ip: '',
  cam_port: 554, onvif_port: 80,
  onvif_username: 'admin', onvif_password: 'admin',
  motion_active: true, retention_days: 30,
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
  { label: 'Retention Days', field: 'retention_days', type: 'number', placeholder: '30' },
]

// ── Shared input style ────────────────────────────────────
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

export default function Cameras() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [form, setForm]         = useState<CameraCreate>(EMPTY)
  const [error, setError]       = useState<string | null>(null)

  const invalidate = () => qc.invalidateQueries({ queryKey: ['cameras'] })

  const { data: cameras = [], isFetching } = useQuery({
    queryKey:       ['cameras'],
    queryFn:        fetchCameras,
    refetchInterval: 15_000,
  })

  const { data: orgs = [] } = useQuery({ queryKey: ['orgs'], queryFn: fetchOrgs })
  const { data: customers = [] } = useQuery({ queryKey: ['customers'], queryFn: fetchCustomers })

  const createMut = useMutation({
    mutationFn: createCamera,
    onSuccess:  () => { invalidate(); setShowForm(false); setForm(EMPTY); setError(null) },
    onError:    (e: Error | unknown) => setError((e as {response?: {data?: {detail?: string}}}).response?.data?.detail ?? 'Failed to create camera'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof updateCamera>[1] }) =>
      updateCamera(id, data),
    onSuccess: () => { invalidate(); setShowForm(false); setIsEditing(false); setForm(EMPTY); setError(null) },
    onError: (e: Error | unknown) => setError((e as {response?: {data?: {detail?: string}}}).response?.data?.detail ?? 'Failed to update camera'),
  })

  const deleteMut = useMutation({ mutationFn: deleteCamera, onSuccess: invalidate })

  function set(field: keyof CameraCreate, value: string | number | boolean) {
    setForm(f => ({ ...f, [field]: value }))
  }

  return (
    <div className="flex flex-col h-full p-4 lg:p-6 gap-5 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            Cameras
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
            {cameras.length} registered · {cameras.filter(c => c.is_online).length} online
            {isFetching && ' · refreshing...'}
          </p>
        </div>
        <button
          onClick={() => {
            if (!showForm || isEditing) {
              setForm(EMPTY); setIsEditing(false); setShowForm(true)
            } else {
              setShowForm(false)
            }
            setError(null)
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
          style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}
          onMouseOver={e => (e.currentTarget.style.filter = 'brightness(1.1)')}
          onMouseOut={e => (e.currentTarget.style.filter = 'none')}
        >
          {showForm && !isEditing ? <X size={13} /> : <Plus size={13} />}
          {showForm && !isEditing ? 'Cancel' : 'Add camera'}
        </button>
      </div>

      {/* Add/Edit form */}
      {showForm && (
        <form
          onSubmit={e => {
            e.preventDefault()
            setError(null)
            if (isEditing) {
              updateMut.mutate({ id: form.cam_id, data: form })
            } else {
              createMut.mutate(form)
            }
          }}
          className="rounded-2xl p-5 grid grid-cols-2 gap-4 shrink-0 animate-[fade-in_0.2s_ease-out]"
          style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}
        >
          <p className="col-span-2 text-sm font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            {isEditing ? `Edit camera: ${form.cam_id}` : 'Register new camera'}
          </p>

          {FIELDS.map(({ label, field, type, placeholder, required }) => (
            <Field key={field} label={label}>
              <input
                type={type}
                placeholder={placeholder}
                required={required}
                disabled={isEditing && field === 'cam_id'}
                value={String(form[field as keyof CameraCreate] ?? '')}
                onChange={e => set(field, type === 'number' ? parseInt(e.target.value) || 0 : e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                style={inputStyle}
                onFocus={e => (e.currentTarget.style.boxShadow = '0 0 0 1.5px oklch(0.78 0.14 200 / 0.6)')}
                onBlur={e => (e.currentTarget.style.boxShadow = '0 0 0 1px var(--color-border)')}
              />
            </Field>
          ))}

          <Field label="Organization">
            <select className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle}
              value={form.organization_id ?? ''}
              onChange={e => set('organization_id', e.target.value ? Number(e.target.value) : undefined as unknown as number)}>
              <option value="">— None —</option>
              {orgs.map(o => <option key={o.id} value={o.id}>{o.code} — {o.name}</option>)}
            </select>
          </Field>
          <Field label="Customer">
            <select className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle}
              value={form.customer_id ?? ''}
              onChange={e => set('customer_id', e.target.value ? Number(e.target.value) : undefined as unknown as number)}>
              <option value="">— None —</option>
              {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </Field>

          <div className="col-span-2 flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={!!form.motion_active}
                onChange={e => set('motion_active', e.target.checked)}
                className="accent-primary"
              />
              <span className="text-xs" style={{ color: 'var(--color-foreground)' }}>Enable motion detection</span>
            </label>
            <div className="flex items-center gap-3">
              {error && <span className="text-xs" style={{ color: 'var(--color-destructive)' }}>{error}</span>}
              <button
                type="submit"
                disabled={createMut.isPending || updateMut.isPending}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
                style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}
              >
                {(createMut.isPending || updateMut.isPending) ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />}
                {createMut.isPending || updateMut.isPending ? 'Saving...' : 'Save camera'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="flex-1 overflow-hidden rounded-2xl flex flex-col min-h-0"
           style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
        {cameras.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <Wifi size={32} style={{ color: 'var(--color-dim)' }} />
            <p className="text-sm" style={{ color: 'var(--color-foreground)' }}>No cameras yet</p>
            <p className="text-xs" style={{ color: 'var(--color-muted-foreground)' }}>Add a camera to start recording</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="text-left text-[11px] font-medium uppercase tracking-widest"
                    style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-muted-foreground)' }}>
                  {['Status', 'Camera ID', 'Name', 'IP', 'Motion', 'Last Seen', ''].map(h => (
                    <th key={h} className={`px-4 py-3 ${h === '' ? 'text-right' : 'text-left'}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cameras.map(cam => (
                  <tr key={cam.cam_id} className="transition-colors last:border-b-0"
                      style={{ borderBottom: '1px solid var(--color-border)' }}
                      onMouseOver={e => (e.currentTarget.style.background = 'oklch(0.28 0.03 260 / 0.4)')}
                      onMouseOut={e => (e.currentTarget.style.background = 'transparent')}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="size-1.5 rounded-full"
                              style={{ background: cam.is_online ? 'var(--color-success)' : 'var(--color-destructive)' }} />
                        <span className="text-[10px] font-mono"
                              style={{ color: cam.is_online ? 'var(--color-success)' : 'var(--color-muted-foreground)' }}>
                          {cam.is_online ? 'Online' : 'Offline'}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--color-foreground)' }}>{cam.cam_id}</td>
                    <td className="px-4 py-3 text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
                      {cam.cam_name ?? <span style={{ color: 'var(--color-dim)', fontStyle: 'italic' }}>—</span>}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
                      {cam.cam_ip}:{cam.cam_port}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => updateMut.mutate({ id: cam.cam_id, data: { motion_active: !cam.motion_active } })}
                        className="font-mono text-[10px] px-2 py-0.5 rounded-md transition-colors"
                        style={{
                          boxShadow: `0 0 0 1px ${cam.motion_active ? 'oklch(0.72 0.17 150 / 0.4)' : 'var(--color-dim)'}`,
                          color: cam.motion_active ? 'var(--color-success)' : 'var(--color-muted-foreground)',
                        }}
                      >
                        {cam.motion_active ? 'ON' : 'OFF'}
                      </button>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
                      {cam.last_seen
                        ? format(new Date(cam.last_seen), 'dd MMM HH:mm:ss')
                        : <span style={{ color: 'var(--color-dim)' }}>Never</span>}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <button
                        onClick={() => {
                          setForm({
                            cam_id: cam.cam_id, cam_name: cam.cam_name ?? '',
                            cam_ip: cam.cam_ip, cam_port: cam.cam_port,
                            onvif_port: cam.onvif_port ?? 80, rtsp_url: cam.rtsp_url ?? '',
                            onvif_username: cam.onvif_username ?? 'admin',
                            onvif_password: cam.onvif_password ?? 'admin',
                            motion_active: cam.motion_active,
                            organization_id: cam.organization_id ?? undefined,
                            customer_id: cam.customer_id ?? undefined,
                            retention_days: cam.retention_days ?? 30,
                          })
                          setIsEditing(true); setShowForm(true); setError(null)
                        }}
                        className="rounded-md p-1.5 mr-2 transition-colors"
                        style={{ color: 'var(--color-muted-foreground)' }}
                        title="Edit Camera"
                      >
                        <Edit2 size={13} />
                      </button>
                      <button
                        onClick={() => { if (confirm(`Remove ${cam.cam_id}?`)) deleteMut.mutate(cam.cam_id) }}
                        className="rounded-md p-1.5 transition-colors"
                        style={{ color: 'var(--color-muted-foreground)' }}
                        title="Deactivate"
                        onMouseOver={e => (e.currentTarget.style.color = 'var(--color-destructive)')}
                        onMouseOut={e => (e.currentTarget.style.color = 'var(--color-muted-foreground)')}
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
