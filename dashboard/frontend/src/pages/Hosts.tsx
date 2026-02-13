import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { hostsApi, CreateHostData } from '../lib/api'
import { useI18n } from '../lib/i18n'
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
  const { t } = useI18n()

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
          <h1 className="text-2xl font-bold text-gray-900">{t('hosts.title')}</h1>
          <p className="text-gray-500">{t('hosts.subtitle')}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            className="btn btn-secondary"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            {t('hosts.sync_docker')}
          </button>
          <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
            <Plus className="h-4 w-4 mr-2" />
            {t('hosts.add_host')}
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">{t('common.loading')}</div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('table.status')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('table.host')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('table.type')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('table.os')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('table.score')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('table.tags')}</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('scans.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {hosts.map((host) => (
                <tr key={host.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className={`h-3 w-3 rounded-full ${
                      host.status === 'online' ? 'bg-success-500' :
                      host.status === 'scanning' ? 'bg-warning-500 animate-pulse' :
                      'bg-gray-400'
                    }`} />
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <Server className="h-5 w-5 text-gray-400" />
                      <span className="font-medium text-gray-900">{host.display_name || host.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-500">{host.host_type}</td>
                  <td className="px-6 py-4 text-gray-500">{host.os_family || t('hosts.unknown_os')}</td>
                  <td className="px-6 py-4">
                    {host.last_scan_score !== null ? (
                      <span className={`badge ${
                        host.last_scan_score >= 80 ? 'badge-success' :
                        host.last_scan_score >= 60 ? 'badge-warning' : 'badge-danger'
                      }`}>
                        {host.last_scan_score}
                      </span>
                    ) : (
                      <span className="text-gray-400">--</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-1">
                      {host.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="badge badge-info">{tag}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => checkStatusMutation.mutate(host.id)}
                        className="btn btn-secondary text-sm py-1 px-2"
                        title={t('hosts.check')}
                      >
                        <Wifi className="h-3 w-3" />
                      </button>
                      <button className="btn btn-secondary text-sm py-1 px-2">
                        <Edit2 className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(t('hosts.delete_confirm'))) {
                            deleteMutation.mutate(host.id)
                          }
                        }}
                        className="btn btn-danger text-sm py-1 px-2"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {hosts.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    {t('hosts.no_hosts')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
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
  const { t } = useI18n()

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
        <h2 className="text-xl font-bold text-gray-900 mb-4">{t('hosts.add_title')}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('hosts.name')}</label>
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
            <label className="block text-sm font-medium text-gray-700">{t('hosts.type')}</label>
            <select
              value={formData.host_type}
              onChange={(e) => setFormData({ ...formData, host_type: e.target.value as 'container' | 'ssh' | 'local' })}
              className="input mt-1"
            >
              <option value="container">{t('hosts.type_container')}</option>
              <option value="ssh">{t('hosts.type_ssh')}</option>
              <option value="local">{t('hosts.type_local')}</option>
            </select>
          </div>
          {formData.host_type === 'ssh' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700">{t('hosts.address')}</label>
                <input
                  type="text"
                  value={formData.address || ''}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="input mt-1"
                  placeholder="192.168.1.100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">{t('hosts.ssh_user')}</label>
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
              {t('common.cancel')}
            </button>
            <button type="submit" disabled={createMutation.isPending} className="btn btn-primary flex-1">
              {createMutation.isPending ? t('hosts.creating') : t('hosts.create_btn')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
