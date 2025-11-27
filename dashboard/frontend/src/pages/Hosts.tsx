import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { hostsApi, CreateHostData } from '../lib/api'
import { Plus, RefreshCw, Server, Trash2, Edit2, Wifi } from 'lucide-react'

interface Host {
  id: number
  name: string
  display_name: string
  host_type: string
  status: string
  os_family: string
  last_scan_score: number | null
  is_active: boolean
  tags: string[]
}

export default function Hosts() {
  const [showAddModal, setShowAddModal] = useState(false)
  const queryClient = useQueryClient()

  const { data: hosts = [], isLoading } = useQuery<Host[]>({
    queryKey: ['hosts'],
    queryFn: async () => {
      const res = await hostsApi.getAll()
      return res.data
    },
  })

  const syncMutation = useMutation({
    mutationFn: hostsApi.syncDocker,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hosts'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: hostsApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hosts'] }),
  })

  const checkStatusMutation = useMutation({
    mutationFn: hostsApi.checkStatus,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hosts'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Hosts</h1>
          <p className="text-gray-500">Manage scan targets</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            className="btn btn-secondary"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            Sync Docker
          </button>
          <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
            <Plus className="h-4 w-4 mr-2" />
            Add Host
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {hosts.map((host) => (
            <div key={host.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <Server className="h-6 w-6 text-gray-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{host.display_name || host.name}</h3>
                    <p className="text-sm text-gray-500">{host.host_type} • {host.os_family || 'Unknown OS'}</p>
                  </div>
                </div>
                <div className={`h-3 w-3 rounded-full ${
                  host.status === 'online' ? 'bg-success-500' :
                  host.status === 'scanning' ? 'bg-warning-500 animate-pulse' :
                  'bg-gray-400'
                }`} />
              </div>

              <div className="mt-4 flex items-center justify-between">
                <div className="flex gap-1">
                  {host.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="badge badge-info">{tag}</span>
                  ))}
                </div>
                {host.last_scan_score !== null && (
                  <span className={`badge ${
                    host.last_scan_score >= 80 ? 'badge-success' :
                    host.last_scan_score >= 60 ? 'badge-warning' : 'badge-danger'
                  }`}>
                    {host.last_scan_score}%
                  </span>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
                <button
                  onClick={() => checkStatusMutation.mutate(host.id)}
                  className="btn btn-secondary flex-1 text-sm py-1"
                >
                  <Wifi className="h-3 w-3 mr-1" />
                  Check
                </button>
                <button className="btn btn-secondary text-sm py-1 px-2">
                  <Edit2 className="h-3 w-3" />
                </button>
                <button
                  onClick={() => {
                    if (confirm('Delete this host?')) {
                      deleteMutation.mutate(host.id)
                    }
                  }}
                  className="btn btn-danger text-sm py-1 px-2"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
          {hosts.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500">
              No hosts configured. Add a host or sync from Docker.
            </div>
          )}
        </div>
      )}

      {showAddModal && <AddHostModal onClose={() => setShowAddModal(false)} />}
    </div>
  )
}

function AddHostModal({ onClose }: { onClose: () => void }) {
  const [formData, setFormData] = useState<CreateHostData>({
    name: '',
    host_type: 'container',
    tags: [],
  })
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: hostsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hosts'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Add Host</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input mt-1"
              placeholder="e.g., target-ubuntu"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Type</label>
            <select
              value={formData.host_type}
              onChange={(e) => setFormData({ ...formData, host_type: e.target.value as 'container' | 'ssh' | 'local' })}
              className="input mt-1"
            >
              <option value="container">Docker Container</option>
              <option value="ssh">SSH Host</option>
              <option value="local">Local</option>
            </select>
          </div>
          {formData.host_type === 'ssh' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700">Address</label>
                <input
                  type="text"
                  value={formData.address || ''}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="input mt-1"
                  placeholder="192.168.1.100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">SSH User</label>
                <input
                  type="text"
                  value={formData.ssh_user || ''}
                  onChange={(e) => setFormData({ ...formData, ssh_user: e.target.value })}
                  className="input mt-1"
                  placeholder="root"
                />
              </div>
            </>
          )}
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="btn btn-secondary flex-1">
              Cancel
            </button>
            <button type="submit" disabled={createMutation.isPending} className="btn btn-primary flex-1">
              {createMutation.isPending ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
