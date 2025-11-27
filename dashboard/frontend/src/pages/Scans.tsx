import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { scansApi, hostsApi, CreateScanData } from '../lib/api'
import { Play, XCircle, CheckCircle, Clock, AlertTriangle, Download } from 'lucide-react'

interface Scan {
  id: number
  host_id: number
  host_name: string
  scanner: string
  status: string
  score: number | null
  passed: number
  failed: number
  warnings: number
  started_at: string
  completed_at: string
  duration_seconds: number | null
}

interface Host {
  id: number
  name: string
}

export default function Scans() {
  const [showNewScan, setShowNewScan] = useState(false)
  const queryClient = useQueryClient()

  const { data: scans = [], isLoading } = useQuery<Scan[]>({
    queryKey: ['scans'],
    queryFn: async () => {
      const res = await scansApi.getAll()
      return res.data
    },
    refetchInterval: 5000,
  })

  const cancelMutation = useMutation({
    mutationFn: scansApi.cancel,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scans'] }),
  })

  const statusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-5 w-5 text-success-500" />
      case 'failed': return <XCircle className="h-5 w-5 text-danger-500" />
      case 'running': return <Clock className="h-5 w-5 text-warning-500 animate-spin" />
      case 'pending': return <Clock className="h-5 w-5 text-gray-400" />
      default: return <AlertTriangle className="h-5 w-5 text-gray-400" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scans</h1>
          <p className="text-gray-500">Security scan history and results</p>
        </div>
        <button onClick={() => setShowNewScan(true)} className="btn btn-primary">
          <Play className="h-4 w-4 mr-2" />
          New Scan
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">Loading...</div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Host</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Scanner</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Results</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {scans.map((scan) => (
                <tr key={scan.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">{statusIcon(scan.status)}</td>
                  <td className="px-6 py-4 font-medium text-gray-900">{scan.host_name}</td>
                  <td className="px-6 py-4 text-gray-500">{scan.scanner}</td>
                  <td className="px-6 py-4">
                    {scan.score !== null ? (
                      <span className={`badge ${
                        scan.score >= 80 ? 'badge-success' :
                        scan.score >= 60 ? 'badge-warning' : 'badge-danger'
                      }`}>{scan.score}%</span>
                    ) : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className="text-success-600">{scan.passed} passed</span>
                    {' / '}
                    <span className="text-danger-600">{scan.failed} failed</span>
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {scan.duration_seconds ? `${scan.duration_seconds}s` : '-'}
                  </td>
                  <td className="px-6 py-4 text-gray-500 text-sm">
                    {scan.started_at ? new Date(scan.started_at).toLocaleString() : '-'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      {scan.status === 'completed' && (
                        <a href={`/api/v1/scans/${scan.id}/report?format=html`} target="_blank" className="btn btn-secondary text-sm py-1 px-2">
                          <Download className="h-3 w-3" />
                        </a>
                      )}
                      {(scan.status === 'running' || scan.status === 'pending') && (
                        <button onClick={() => cancelMutation.mutate(scan.id)} className="btn btn-danger text-sm py-1 px-2">
                          <XCircle className="h-3 w-3" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {scans.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                    No scans yet. Start a new scan to see results.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showNewScan && <NewScanModal onClose={() => setShowNewScan(false)} />}
    </div>
  )
}

function NewScanModal({ onClose }: { onClose: () => void }) {
  const [formData, setFormData] = useState<CreateScanData>({
    host_id: 0,
    scanner: 'lynis',
  })
  const queryClient = useQueryClient()

  const { data: hosts = [] } = useQuery<Host[]>({
    queryKey: ['hosts'],
    queryFn: async () => {
      const res = await hostsApi.getAll()
      return res.data
    },
  })

  const createMutation = useMutation({
    mutationFn: scansApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (formData.host_id) createMutation.mutate(formData)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">New Scan</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Host</label>
            <select
              required
              value={formData.host_id}
              onChange={(e) => setFormData({ ...formData, host_id: Number(e.target.value) })}
              className="input mt-1"
            >
              <option value="">Select host...</option>
              {hosts.map((host) => (
                <option key={host.id} value={host.id}>{host.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Scanner</label>
            <select
              value={formData.scanner}
              onChange={(e) => setFormData({ ...formData, scanner: e.target.value as 'lynis' | 'openscap' | 'trivy' | 'atomic' })}
              className="input mt-1"
            >
              <option value="lynis">Lynis</option>
              <option value="openscap">OpenSCAP</option>
              <option value="trivy">Trivy</option>
              <option value="atomic">Atomic Red Team</option>
            </select>
          </div>
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="btn btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={createMutation.isPending || !formData.host_id} className="btn btn-primary flex-1">
              {createMutation.isPending ? 'Starting...' : 'Start Scan'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
