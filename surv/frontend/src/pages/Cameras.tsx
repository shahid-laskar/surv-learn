import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { Plus, Trash2, X, Check, Wifi, Edit2, Loader2 } from 'lucide-react'
import { fetchCameras, createCamera, updateCamera, deleteCamera, fetchOrgs, fetchCustomers, type CameraCreate } from '../api/client'

type StreamProtocol = 'rtsp' | 'rtsps' | 'rtmp'

const EMPTY: CameraCreate = {
  cam_id: '', cam_name: '', cam_ip: '',
  cam_port: 554, onvif_port: 80,
  stream_protocol: 'rtsp',
  onvif_username: 'admin', onvif_password: 'admin',
  motion_active: true, retention_days: 30,
}

const DEFAULT_PORTS: Record<StreamProtocol, number> = {
  rtsp: 554,
  rtsps: 322,
  rtmp: 1935,
}

const URL_PLACEHOLDERS: Record<StreamProtocol, string> = {
  rtsp:  'rtsp://IP:PORT/PATH',
  rtsps: 'rtsps://IP:PORT/PATH',
  rtmp:  '',
}

function rtmpPublishUrl(camId: string): string {
  const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
  return `rtmp://${host}:1935/${camId}`
}

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

  function setProtocol(protocol: StreamProtocol) {
    setForm(f => ({
      ...f,
      stream_protocol: protocol,
      cam_port: DEFAULT_PORTS[protocol],
      rtsp_url: protocol === 'rtmp' ? '' : f.rtsp_url,
      motion_active: protocol === 'rtmp' ? false : f.motion_active,
    }))
  }

  const protocol = (form.stream_protocol ?? 'rtsp') as StreamProtocol
  const isRtmp = protocol === 'rtmp'

  function validateAndSubmit() {
    setError(null)
    if (!isRtmp) {
      const url = (form.rtsp_url ?? '').trim()
      if (!url) {
        setError('Stream URL is required for RTSP/RTSPS cameras')
        return
      }
      const expected = `${protocol}://`
      if (!url.toLowerCase().startsWith(expected)) {
        setError(`Stream URL must start with ${expected}`)
        return
      }
    }
    const payload: CameraCreate = {
      ...form,
      stream_protocol: protocol,
      rtsp_url: isRtmp ? undefined : form.rtsp_url,
    }
    if (isEditing) {
      updateMut.mutate({ id: form.cam_id, data: payload })
    } else {
      createMut.mutate(payload)
    }
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
            validateAndSubmit()
          }}
          className="rounded-2xl p-5 grid grid-cols-2 gap-4 shrink-0 animate-[fade-in_0.2s_ease-out]"
          style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}
        >
          <p className="col-span-2 text-sm font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            {isEditing ? `Edit camera: ${form.cam_id}` : 'Register new camera'}
          </p>

          <Field label="Camera ID">
            <input
              type="text"
              placeholder="CAMKRTVM00001"
              required
              disabled={isEditing}
              value={form.cam_id}
              onChange={e => set('cam_id', e.target.value)}
              className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              style={inputStyle}
            />
          </Field>
          <Field label="Name">
            <input
              type="text"
              placeholder="Main Entrance"
              value={form.cam_name ?? ''}
              onChange={e => set('cam_name', e.target.value)}
              className="w-full rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
            />
          </Field>
          <Field label="IP Address">
            <input
              type="text"
              placeholder="192.168.1.100"
              required
              value={form.cam_ip}
              onChange={e => set('cam_ip', e.target.value)}
              className="w-full rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
            />
          </Field>
          <Field label="Stream protocol">
            <select
              className="w-full rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
              value={protocol}
              onChange={e => setProtocol(e.target.value as StreamProtocol)}
            >
              <option value="rtsp">RTSP (pull)</option>
              <option value="rtsps">RTSPS (pull TLS)</option>
              <option value="rtmp">RTMP (camera publishes)</option>
            </select>
          </Field>
          {!isRtmp && (
            <Field label={protocol === 'rtsps' ? 'RTSPS Port' : 'RTSP Port'}>
              <input
                type="number"
                placeholder={String(DEFAULT_PORTS[protocol])}
                value={form.cam_port ?? DEFAULT_PORTS[protocol]}
                onChange={e => set('cam_port', parseInt(e.target.value) || 0)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              />
            </Field>
          )}
          <Field label="ONVIF Port">
            <input
              type="number"
              placeholder="80"
              value={form.onvif_port ?? 80}
              onChange={e => set('onvif_port', parseInt(e.target.value) || 0)}
              className="w-full rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
            />
          </Field>

          {isRtmp ? (
            <div className="col-span-2 rounded-lg px-3 py-2 text-xs font-mono"
                 style={{ ...inputStyle, color: 'var(--color-muted-foreground)' }}>
              Configure the camera/encoder to publish to:{' '}
              <span style={{ color: 'var(--color-foreground)' }}>
                {form.cam_id ? rtmpPublishUrl(form.cam_id) : 'rtmp://&lt;host&gt;:1935/&lt;cam_id&gt;'}
              </span>
            </div>
          ) : (
            <Field label="Stream URL">
              <input
                type="text"
                placeholder={URL_PLACEHOLDERS[protocol]}
                required
                value={form.rtsp_url ?? ''}
                onChange={e => set('rtsp_url', e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              />
            </Field>
          )}

          <Field label="Username">
            <input
              type="text"
              placeholder="admin"
              value={form.onvif_username ?? ''}
              onChange={e => set('onvif_username', e.target.value)}
              className="w-full rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
            />
          </Field>
          <Field label="Password">
            <input
              type="password"
              placeholder="••••••"
              value={form.onvif_password ?? ''}
              onChange={e => set('onvif_password', e.target.value)}
              className="w-full rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
            />
          </Field>
          <Field label="Retention Days">
            <input
              type="number"
              placeholder="30"
              value={form.retention_days ?? 30}
              onChange={e => set('retention_days', parseInt(e.target.value) || 0)}
              className="w-full rounded-lg px-3 py-2 text-sm outline-none"
              style={inputStyle}
            />
          </Field>

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
                disabled={isRtmp}
              />
              <span className="text-xs" style={{ color: 'var(--color-foreground)' }}>
                Enable motion detection{isRtmp ? ' (N/A for RTMP)' : ''}
              </span>
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
                  {['Status', 'Camera ID', 'Name', 'Protocol', 'IP', 'Motion', 'Last Seen', ''].map(h => (
                    <th key={h} className={`px-4 py-3 ${h === '' ? 'text-right' : 'text-left'}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cameras.map(cam => {
                  const camProto = (cam.stream_protocol ?? 'rtsp') as StreamProtocol
                  return (
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
                    <td className="px-4 py-3 font-mono text-[10px] uppercase" style={{ color: 'var(--color-muted-foreground)' }}
                        title={camProto === 'rtmp' ? rtmpPublishUrl(cam.cam_id) : (cam.rtsp_url ?? '')}>
                      {camProto}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
                      {cam.cam_ip}{camProto !== 'rtmp' ? `:${cam.cam_port}` : ''}
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
                            onvif_port: cam.onvif_port ?? 80,
                            stream_protocol: camProto,
                            rtsp_url: cam.rtsp_url ?? '',
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
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
