import { useState } from 'react'
import { Server, Plus, Trash2, Shield, Activity, HardDrive, RefreshCw } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchFleetNodes, provisionNvr, decommissionNvr, type NvrNode } from '../api/client'
import { formatDistanceToNow } from 'date-fns'

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

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
            <Server size={20} className="text-accent" />
            NVR Fleet
          </h1>
          <p className="text-sm text-muted mt-1">Manage Edge NVR appliances and zero-touch provisioning.</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded font-medium text-sm flex items-center gap-2 transition-colors"
        >
          <Plus size={16} />
          Provision NVR
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48 text-muted">Loading fleet data...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {nodes.map(node => (
            <div key={node.id} className="bg-panel border border-border rounded-lg p-5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-slate-200">{node.site_code}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`size-2 rounded-full ${node.is_provisioned ? (node.last_heartbeat && new Date(node.last_heartbeat).getTime() > Date.now() - 120000 ? 'bg-online' : 'bg-alert') : 'bg-muted'}`} />
                    <span className="text-xs text-muted">
                      {!node.is_provisioned 
                        ? 'Pending Provisioning' 
                        : (node.last_heartbeat ? `Last seen ${formatDistanceToNow(new Date(node.last_heartbeat))} ago` : 'Never seen')}
                    </span>
                  </div>
                </div>
                <button 
                  onClick={() => {
                    if (confirm(`Are you sure you want to decommission NVR for site ${node.site_code}?`)) {
                      decommissionMutation.mutate(node.site_code)
                    }
                  }}
                  className="text-muted hover:text-alert p-1"
                  title="Decommission NVR"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              <div className="space-y-3 mb-5">
                <div className="flex items-center gap-2 text-sm text-slate-300">
                  <Shield size={14} className="text-muted" />
                  <span className="text-muted">Overlay IP:</span>
                  <span className="font-mono bg-surface px-1.5 py-0.5 rounded text-xs">{node.overlay_ip || 'Unassigned'}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-300">
                  <HardDrive size={14} className="text-muted" />
                  <span className="text-muted">Disk Usage:</span>
                  <div className="flex-1 bg-surface rounded-full h-1.5 overflow-hidden ml-2">
                    <div 
                      className={`h-full ${node.disk_used_pct && node.disk_used_pct > 85 ? 'bg-alert' : 'bg-accent'}`} 
                      style={{ width: `${node.disk_used_pct || 0}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono w-10 text-right">{node.disk_used_pct || 0}%</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-300">
                  <Activity size={14} className="text-muted" />
                  <span className="text-muted">Cameras:</span>
                  <span className="font-semibold">{node.camera_count}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-300">
                  <RefreshCw size={14} className="text-muted" />
                  <span className="text-muted">Agent Version:</span>
                  <span className="font-mono text-xs">{node.agent_version || 'Unknown'}</span>
                </div>
              </div>

              {!node.is_provisioned && (
                <div className="mt-4 p-3 bg-surface border border-border rounded text-sm">
                  <p className="text-muted mb-2 text-xs uppercase tracking-wider font-semibold">Enrollment</p>
                  <p className="text-[10px] text-muted">Set SITE_CODE and SITE_TOKEN in edge-nvr/.env on the site appliance.</p>
                </div>
              )}
            </div>
          ))}
          
          {nodes.length === 0 && (
            <div className="col-span-full py-12 text-center border border-dashed border-border rounded-lg text-muted">
              <Server size={32} className="mx-auto mb-3 opacity-50" />
              <p>No NVRs deployed in the fleet yet.</p>
            </div>
          )}
        </div>
      )}

      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-panel border border-border rounded-lg w-full max-w-md p-6">
            <h2 className="text-lg font-semibold text-slate-100 mb-4">
              {provisionedToken ? 'NVR Provisioned' : 'Provision New NVR'}
            </h2>
            {provisionedToken ? (
              <div className="space-y-4">
                <p className="text-sm text-muted">Copy into <code className="text-accent">edge-nvr/.env</code> on the site VM:</p>
                <pre className="bg-surface border border-border rounded p-3 text-xs text-slate-300 overflow-x-auto select-all">
{`SITE_CODE=${newSiteCode}\nSITE_TOKEN=${provisionedToken}\nHUB_API_URL=http://<hub-ip>:8000/api/v1`}
                </pre>
                <button
                  type="button"
                  onClick={() => {
                    setProvisionedToken(null)
                    setShowAddModal(false)
                    setNewSiteCode('')
                    setNewCustomerSiteId('')
                    setNewHardware('')
                  }}
                  className="bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded text-sm font-medium w-full"
                >
                  Done
                </button>
              </div>
            ) : (
            <form onSubmit={handleProvision} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Site Code</label>
                <input
                  type="text"
                  required
                  value={newSiteCode}
                  onChange={e => setNewSiteCode(e.target.value)}
                  className="w-full bg-surface border border-border rounded p-2 text-sm text-slate-200 outline-none focus:border-accent"
                  placeholder="e.g. BLR-WH-01"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Customer Site ID</label>
                <input
                  type="number"
                  required
                  value={newCustomerSiteId}
                  onChange={e => setNewCustomerSiteId(e.target.value)}
                  className="w-full bg-surface border border-border rounded p-2 text-sm text-slate-200 outline-none focus:border-accent"
                  placeholder="Numeric ID"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Hardware Label (Optional)</label>
                <input
                  type="text"
                  value={newHardware}
                  onChange={e => setNewHardware(e.target.value)}
                  className="w-full bg-surface border border-border rounded p-2 text-sm text-slate-200 outline-none focus:border-accent"
                  placeholder="e.g. Intel N100, RPi5"
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={provisionMutation.isPending}
                  className="bg-accent hover:bg-accent/90 text-white px-4 py-2 rounded text-sm font-medium"
                >
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
