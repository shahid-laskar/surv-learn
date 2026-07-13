import { useState } from 'react'
import { Server, Plus, Trash2, Shield, Activity, HardDrive, RefreshCw, Loader2 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchFleetNodes, provisionNvr, decommissionNvr, type NvrNode } from '../api/client'
import { formatDistanceToNow } from 'date-fns'

function isRecentHeartbeat(ts: string | null | undefined) {
  if (!ts) return false
  return new Date(ts).getTime() > Date.now() - 120_000
}

export default function NvrFleet() {
  const queryClient = useQueryClient()
  const [showAddModal, setShowAddModal] = useState(false)
  const [newSiteCode, setNewSiteCode] = useState('')
  const [newCustomerSiteId, setNewCustomerSiteId] = useState('')
  const [newHardware, setNewHardware] = useState('')
  const [provisionedToken, setProvisionedToken] = useState<string | null>(null)

  const { data: nodes = [], isLoading } = useQuery<NvrNode[]>({
    queryKey: ['fleet-nodes'],
    queryFn: fetchFleetNodes,
    refetchInterval: 30000,
  })

  const provisionMutation = useMutation({
    mutationFn: provisionNvr,
    onSuccess: (node) => {
      queryClient.invalidateQueries({ queryKey: ['fleet-nodes'] })
      if (node.site_token) {
        setProvisionedToken(node.site_token)
      } else {
        setShowAddModal(false)
        setNewSiteCode('')
        setNewCustomerSiteId('')
        setNewHardware('')
      }
    },
  })

  const decommissionMutation = useMutation({
    mutationFn: decommissionNvr,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fleet-nodes'] })
    },
  })

  const handleProvision = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSiteCode || !newCustomerSiteId) return
    provisionMutation.mutate({
      site_code: newSiteCode,
      customer_site_id: parseInt(newCustomerSiteId),
      hardware_label: newHardware || undefined,
    })
  }

  const inputStyle = {
    background: 'oklch(0.28 0.03 260 / 0.5)',
    color: 'var(--color-foreground)',
    boxShadow: '0 0 0 1px var(--color-border)',
  } as React.CSSProperties

  return (
    <div className="flex flex-col h-full p-4 lg:p-6 gap-5 animate-[fade-in_0.2s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-semibold flex items-center gap-2"
              style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
            <Server size={16} style={{ color: 'var(--color-primary)' }} />
            NVR Fleet
          </h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-muted-foreground)' }}>
            Manage Edge NVR appliances and zero-touch provisioning.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
          style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}
          onMouseOver={e => (e.currentTarget.style.filter = 'brightness(1.1)')}
          onMouseOut={e => (e.currentTarget.style.filter = 'none')}
        >
          <Plus size={14} />
          Provision NVR
        </button>
      </div>

      {/* Cards */}
      {isLoading ? (
        <div className="flex items-center justify-center h-48"
             style={{ color: 'var(--color-muted-foreground)' }}>
          <Loader2 size={18} className="animate-spin mr-2" style={{ color: 'var(--color-primary)' }} />
          Loading fleet data...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {nodes.map(node => {
            const heartbeatOk = node.is_provisioned && isRecentHeartbeat(node.last_heartbeat)
            const dotColor = !node.is_provisioned
              ? 'var(--color-muted-foreground)'
              : heartbeatOk
              ? 'var(--color-success)'
              : 'var(--color-destructive)'

            return (
              <div key={node.id} className="rounded-2xl p-5"
                   style={{ background: 'oklch(0.22 0.035 260 / 0.5)', boxShadow: '0 0 0 1px var(--color-border)' }}>
                {/* Top row */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
                      {node.site_code}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="relative flex size-2">
                        {heartbeatOk && (
                          <span className="absolute inline-flex h-full w-full rounded-full opacity-60 animate-ping"
                                style={{ background: dotColor }} />
                        )}
                        <span className="relative size-2 rounded-full" style={{ background: dotColor }} />
                      </span>
                      <span className="text-xs" style={{ color: 'var(--color-muted-foreground)' }}>
                        {!node.is_provisioned
                          ? 'Pending Provisioning'
                          : node.last_heartbeat
                          ? `Last seen ${formatDistanceToNow(new Date(node.last_heartbeat))} ago`
                          : 'Never seen'}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm(`Decommission NVR for site ${node.site_code}?`)) {
                        decommissionMutation.mutate(node.site_code)
                      }
                    }}
                    className="rounded-lg p-1.5 transition-colors"
                    style={{ color: 'var(--color-muted-foreground)' }}
                    title="Decommission NVR"
                    onMouseOver={e => (e.currentTarget.style.color = 'var(--color-destructive)')}
                    onMouseOut={e => (e.currentTarget.style.color = 'var(--color-muted-foreground)')}
                  >
                    <Trash2 size={15} />
                  </button>
                </div>

                {/* Details */}
                <div className="space-y-3 mb-4">
                  <div className="flex items-center gap-2 text-sm">
                    <Shield size={13} style={{ color: 'var(--color-muted-foreground)' }} />
                    <span className="text-xs" style={{ color: 'var(--color-muted-foreground)' }}>Overlay IP:</span>
                    <span className="font-mono text-xs px-1.5 py-0.5 rounded-md"
                          style={{ background: 'var(--color-panel)', color: 'var(--color-foreground)' }}>
                      {node.overlay_ip || 'Unassigned'}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <HardDrive size={13} style={{ color: 'var(--color-muted-foreground)' }} />
                    <span className="text-xs" style={{ color: 'var(--color-muted-foreground)' }}>Disk:</span>
                    <div className="flex-1 rounded-full h-1.5 overflow-hidden"
                         style={{ background: 'var(--color-panel)' }}>
                      <div
                        className="h-full transition-all rounded-full"
                        style={{
                          width: `${node.disk_used_pct || 0}%`,
                          background: node.disk_used_pct && node.disk_used_pct > 85
                            ? 'var(--color-destructive)'
                            : 'var(--color-primary)',
                        }}
                      />
                    </div>
                    <span className="font-mono text-xs w-10 text-right" style={{ color: 'var(--color-foreground)' }}>
                      {node.disk_used_pct || 0}%
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <Activity size={13} style={{ color: 'var(--color-muted-foreground)' }} />
                    <span style={{ color: 'var(--color-muted-foreground)' }}>Cameras:</span>
                    <span className="font-semibold" style={{ color: 'var(--color-foreground)' }}>{node.camera_count}</span>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <RefreshCw size={13} style={{ color: 'var(--color-muted-foreground)' }} />
                    <span style={{ color: 'var(--color-muted-foreground)' }}>Agent:</span>
                    <span className="font-mono" style={{ color: 'var(--color-foreground)' }}>
                      {node.agent_version || 'Unknown'}
                    </span>
                  </div>
                </div>

                {!node.is_provisioned && (
                  <div className="mt-2 p-3 rounded-xl text-xs"
                       style={{ background: 'var(--color-panel)', border: '1px solid var(--color-border)' }}>
                    <p className="font-mono text-[10px] uppercase tracking-wider font-semibold mb-1"
                       style={{ color: 'var(--color-muted-foreground)' }}>Enrollment</p>
                    <p style={{ color: 'var(--color-muted-foreground)' }}>
                      Set SITE_CODE and SITE_TOKEN in edge-nvr/.env on the site appliance.
                    </p>
                  </div>
                )}
              </div>
            )
          })}

          {nodes.length === 0 && (
            <div className="col-span-full py-16 text-center rounded-2xl"
                 style={{ border: '1px dashed var(--color-border)', color: 'var(--color-muted-foreground)' }}>
              <Server size={32} className="mx-auto mb-3 opacity-40" />
              <p className="text-sm">No NVRs deployed in the fleet yet.</p>
            </div>
          )}
        </div>
      )}

      {/* Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
             style={{ background: 'rgba(0,0,0,0.6)' }}>
          <div className="w-full max-w-md rounded-2xl p-6 animate-[fade-in_0.2s_ease-out]"
               style={{
                 background: 'oklch(0.22 0.035 260 / 0.95)',
                 boxShadow: '0 0 0 1px var(--color-border)',
                 backdropFilter: 'blur(16px)',
               }}>
            <h2 className="text-lg font-semibold mb-4"
                style={{ fontFamily: 'var(--font-display)', color: 'var(--color-foreground)' }}>
              {provisionedToken ? 'NVR Provisioned' : 'Provision New NVR'}
            </h2>

            {provisionedToken ? (
              <div className="space-y-4">
                <p className="text-sm" style={{ color: 'var(--color-muted-foreground)' }}>
                  Copy into <code className="text-xs px-1 py-0.5 rounded"
                                  style={{ background: 'var(--color-panel)', color: 'var(--color-primary)' }}>
                    edge-nvr/.env
                  </code> on the site VM:
                </p>
                <pre className="rounded-xl p-3 text-xs overflow-x-auto select-all"
                     style={{ background: 'var(--color-panel)', border: '1px solid var(--color-border)', color: 'var(--color-foreground)' }}>
{`SITE_CODE=${newSiteCode}\nSITE_TOKEN=${provisionedToken}\nHUB_API_URL=http://<hub-ip>:8000/api/v1`}
                </pre>
                <button
                  type="button"
                  onClick={() => {
                    setProvisionedToken(null)
                    setShowAddModal(false)
                    setNewSiteCode(''); setNewCustomerSiteId(''); setNewHardware('')
                  }}
                  className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
                  style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleProvision} className="space-y-4">
                {[
                  { label: 'Site Code', value: newSiteCode, set: setNewSiteCode, type: 'text', placeholder: 'e.g. BLR-WH-01', required: true },
                  { label: 'Customer Site ID', value: newCustomerSiteId, set: setNewCustomerSiteId, type: 'number', placeholder: 'Numeric ID', required: true },
                  { label: 'Hardware Label (Optional)', value: newHardware, set: setNewHardware, type: 'text', placeholder: 'e.g. Intel N100, RPi5' },
                ].map(({ label, value, set, type, placeholder, required }) => (
                  <div key={label}>
                    <label className="block text-xs font-medium uppercase tracking-widest mb-1.5"
                           style={{ color: 'var(--color-muted-foreground)' }}>
                      {label}
                    </label>
                    <input
                      type={type}
                      required={required}
                      value={value}
                      onChange={e => set(e.target.value)}
                      className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all"
                      style={inputStyle}
                      onFocus={e => (e.currentTarget.style.boxShadow = '0 0 0 1.5px oklch(0.78 0.14 200 / 0.6)')}
                      onBlur={e => (e.currentTarget.style.boxShadow = '0 0 0 1px var(--color-border)')}
                      placeholder={placeholder}
                    />
                  </div>
                ))}
                <div className="flex justify-end gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 text-sm font-medium rounded-lg transition-colors"
                    style={{ color: 'var(--color-muted-foreground)' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={provisionMutation.isPending}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-60"
                    style={{ background: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}
                  >
                    {provisionMutation.isPending && <Loader2 size={13} className="animate-spin" />}
                    {provisionMutation.isPending ? 'Provisioning...' : 'Provision NVR'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
