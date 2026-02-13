import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { schedulesApi, hostsApi, CreateScheduleData } from '../lib/api'
import { useI18n } from '../lib/i18n'
import { Plus, Calendar, Trash2, Play, Pause } from 'lucide-react'

interface Schedule {
  id: number
  host_id: number
  name: string
  scanner: string
  cron_expression: string
  is_active: boolean
  last_run_at: string | null
  next_run_at: string | null
  run_count: number
}

interface Host {
  id: number
  name: string
}

export default function Schedules() {
  const [showAdd, setShowAdd] = useState(false)
  const queryClient = useQueryClient()
  const { t } = useI18n()

  const { data: schedules = [], isLoading } = useQuery<Schedule[]>({
    queryKey: ['schedules'],
    queryFn: async () => {
      const res = await schedulesApi.getAll({ active_only: false })
      return res.data
    },
  })

  const toggleMutation = useMutation({
    mutationFn: schedulesApi.toggle,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['schedules'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: schedulesApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['schedules'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('schedules.title')}</h1>
          <p className="text-gray-500">{t('schedules.subtitle')}</p>
        </div>
        <button onClick={() => setShowAdd(true)} className="btn btn-primary">
          <Plus className="h-4 w-4 mr-2" />
          {t('schedules.add')}
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">{t('common.loading')}</div>
      ) : (
        <div className="grid gap-4">
          {schedules.map((schedule) => (
            <div key={schedule.id} className="card">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg ${schedule.is_active ? 'bg-success-50' : 'bg-gray-100'}`}>
                    <Calendar className={`h-6 w-6 ${schedule.is_active ? 'text-success-600' : 'text-gray-400'}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{schedule.name}</h3>
                    <p className="text-sm text-gray-500">
                      {schedule.scanner} • <code className="bg-gray-100 px-1 rounded">{schedule.cron_expression}</code>
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right text-sm">
                    <p className="text-gray-500">{t('schedules.runs')}: {schedule.run_count}</p>
                    {schedule.next_run_at && (
                      <p className="text-gray-400">{t('schedules.next')}: {new Date(schedule.next_run_at).toLocaleString()}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => toggleMutation.mutate(schedule.id)}
                      className={`btn ${schedule.is_active ? 'btn-secondary' : 'btn-primary'} text-sm py-1 px-2`}
                    >
                      {schedule.is_active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                    </button>
                    <button
                      onClick={() => confirm(t('schedules.delete_confirm')) && deleteMutation.mutate(schedule.id)}
                      className="btn btn-danger text-sm py-1 px-2"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {schedules.length === 0 && (
            <div className="text-center py-12 text-gray-500">{t('schedules.no_schedules')}</div>
          )}
        </div>
      )}

      {showAdd && <AddScheduleModal onClose={() => setShowAdd(false)} />}
    </div>
  )
}

function AddScheduleModal({ onClose }: { onClose: () => void }) {
  const [formData, setFormData] = useState<CreateScheduleData>({
    host_id: 0,
    name: '',
    scanner: 'lynis',
    cron_expression: '0 2 * * *',
  })
  const queryClient = useQueryClient()
  const { t } = useI18n()

  const { data: hosts = [] } = useQuery<Host[]>({
    queryKey: ['hosts'],
    queryFn: async () => (await hostsApi.getAll()).data,
  })

  const createMutation = useMutation({
    mutationFn: schedulesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      onClose()
    },
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">{t('schedules.add_title')}</h2>
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(formData) }} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('schedules.name')}</label>
            <input type="text" required value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="input mt-1" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('schedules.host')}</label>
            <select required value={formData.host_id} onChange={(e) => setFormData({ ...formData, host_id: Number(e.target.value) })} className="input mt-1">
              <option value="">{t('scans.select_host')}</option>
              {hosts.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('schedules.scanner')}</label>
            <select value={formData.scanner} onChange={(e) => setFormData({ ...formData, scanner: e.target.value })} className="input mt-1">
              <option value="lynis">Lynis</option>
              <option value="openscap">OpenSCAP</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('schedules.cron')}</label>
            <input type="text" required value={formData.cron_expression} onChange={(e) => setFormData({ ...formData, cron_expression: e.target.value })} className="input mt-1" placeholder="0 2 * * *" />
            <p className="text-xs text-gray-500 mt-1">{t('schedules.cron_hint')}</p>
          </div>
          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="btn btn-secondary flex-1">{t('common.cancel')}</button>
            <button type="submit" disabled={createMutation.isPending} className="btn btn-primary flex-1">{t('common.create')}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
