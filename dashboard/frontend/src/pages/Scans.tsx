import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { scansApi, hostsApi } from '../lib/api'
import { useI18n } from '../lib/i18n'
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
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const queryClient = useQueryClient()
  const { t } = useI18n()

  const { data: scans = [], isLoading } = useQuery<Scan[]>({
    queryKey: ['scans'],
    queryFn: async () => {
      const res = await scansApi.getAll({ limit: 500 })
      return res.data
    },
    refetchInterval: 5000,
  })

  const cancelMutation = useMutation({
    mutationFn: scansApi.cancel,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scans'] }),
  })

  const filteredScans = scans.filter((scan) => {
    if (dateFrom && scan.started_at) {
      const scanDate = new Date(scan.started_at).toISOString().slice(0, 10)
      if (scanDate < dateFrom) return false
    }
    if (dateTo && scan.started_at) {
      const scanDate = new Date(scan.started_at).toISOString().slice(0, 10)
      if (scanDate > dateTo) return false
    }
    return true
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
          <h1 className="text-2xl font-bold text-gray-900">{t('scans.title')}</h1>
          <p className="text-gray-500">{t('scans.subtitle')}</p>
        </div>
        <button onClick={() => setShowNewScan(true)} className="btn btn-primary">
          <Play className="h-4 w-4 mr-2" />
          {t('scans.new_scan')}
        </button>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500">{t('scans.date_from')}:</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="text-sm border border-gray-300 rounded-lg px-2 py-1 bg-white text-gray-700"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500">{t('scans.date_to')}:</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="text-sm border border-gray-300 rounded-lg px-2 py-1 bg-white text-gray-700"
          />
        </div>
        {(dateFrom || dateTo) && (
          <button
            onClick={() => { setDateFrom(''); setDateTo('') }}
            className="text-sm text-gray-400 hover:text-gray-600"
          >
            {t('common.clear')}
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-12">{t('common.loading')}</div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('scans.status')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('scans.host')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('scans.scanner')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('scans.score')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('scans.results')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('scans.duration')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('scans.started')}</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('scans.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredScans.map((scan) => (
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
                    <span className="text-success-600">{scan.passed} {t('scans.passed')}</span>
                    {' / '}
                    <span className="text-danger-600">{scan.failed} {t('scans.failed')}</span>
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
                    {t('scans.no_scans')}
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
  const [hostId, setHostId] = useState<number>(-1)
  const [scanner, setScanner] = useState<string>('lynis')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [progress, setProgress] = useState('')
  const queryClient = useQueryClient()
  const { t } = useI18n()

  const { data: hosts = [] } = useQuery<Host[]>({
    queryKey: ['hosts'],
    queryFn: async () => {
      const res = await hostsApi.getAll()
      return res.data
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (hostId === -1 && hosts.length === 0) return
    if (hostId === 0 && hosts.length === 0) return

    setIsSubmitting(true)

    try {
      if (hostId === -1) {
        // All hosts
        for (let i = 0; i < hosts.length; i++) {
          const host = hosts[i]
          setProgress(`${i + 1} / ${hosts.length}: ${host.name}`)
          try {
            await scansApi.create({
              host_id: host.id,
              scanner: scanner as 'lynis' | 'openscap' | 'trivy' | 'atomic',
            })
          } catch {
            // Continue with other hosts if one fails
          }
        }
      } else {
        await scansApi.create({
          host_id: hostId,
          scanner: scanner as 'lynis' | 'openscap' | 'trivy' | 'atomic',
        })
      }
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      onClose()
    } catch {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">{t('scans.new_title')}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('scans.host')}</label>
            <select
              required
              value={hostId}
              onChange={(e) => setHostId(Number(e.target.value))}
              className="input mt-1"
            >
              <option value={0}>{t('scans.select_host')}</option>
              <option value={-1}>{t('scans.all_hosts')}</option>
              {hosts.map((host) => (
                <option key={host.id} value={host.id}>{host.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('scans.scanner')}</label>
            <select
              value={scanner}
              onChange={(e) => setScanner(e.target.value)}
              className="input mt-1"
            >
              <option value="lynis">Lynis</option>
              <option value="openscap">OpenSCAP</option>
              <option value="trivy">Trivy</option>
              <option value="atomic">Atomic Red Team</option>
            </select>
          </div>
          {progress && (
            <p className="text-sm text-gray-500">{progress}</p>
          )}
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} disabled={isSubmitting} className="btn btn-secondary flex-1">{t('common.cancel')}</button>
            <button type="submit" disabled={isSubmitting || hostId === 0} className="btn btn-primary flex-1">
              {isSubmitting ? t('scans.starting') : t('scans.start_btn')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
