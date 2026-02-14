import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { schedulesApi, hostsApi } from '../lib/api'
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

type Frequency = 'daily' | 'weekly' | 'monthly' | 'yearly'

const SCANNERS = ['lynis', 'openscap', 'trivy', 'atomic']

function buildCron(freq: Frequency, time: string, days: number[], dayOfMonth: number, month: number): string {
  const [h, m] = time.split(':').map(Number)
  switch (freq) {
    case 'daily':
      if (days.length === 0 || days.length === 7) return `${m} ${h} * * *`
      return `${m} ${h} * * ${days.join(',')}`
    case 'weekly':
      return `${m} ${h} * * ${days.length > 0 ? days[0] : 1}`
    case 'monthly':
      return `${m} ${h} ${dayOfMonth} * *`
    case 'yearly':
      return `${m} ${h} ${dayOfMonth} ${month} *`
  }
}

function AddScheduleModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState('')
  const [hostId, setHostId] = useState<number | 'all'>(0)
  const [scanner, setScanner] = useState<string | 'all'>('lynis')
  const [freq, setFreq] = useState<Frequency>('daily')
  const [time, setTime] = useState('02:00')
  const [days, setDays] = useState<number[]>([])
  const [dayOfMonth, setDayOfMonth] = useState(1)
  const [month, setMonth] = useState(1)
  const [submitting, setSubmitting] = useState(false)

  const queryClient = useQueryClient()
  const { t } = useI18n()

  const { data: hosts = [] } = useQuery<Host[]>({
    queryKey: ['hosts'],
    queryFn: async () => (await hostsApi.getAll()).data,
  })

  const dayKeys: Array<{ key: string; num: number }> = [
    { key: 'schedules.mon', num: 1 },
    { key: 'schedules.tue', num: 2 },
    { key: 'schedules.wed', num: 3 },
    { key: 'schedules.thu', num: 4 },
    { key: 'schedules.fri', num: 5 },
    { key: 'schedules.sat', num: 6 },
    { key: 'schedules.sun', num: 0 },
  ]

  const toggleDay = (num: number) => {
    setDays((prev) => prev.includes(num) ? prev.filter((d) => d !== num) : [...prev, num])
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)

    const cron = buildCron(freq, time, days, dayOfMonth, month)
    const hostIds = hostId === 'all' ? hosts.map((h) => h.id) : [hostId]
    const scanners = scanner === 'all' ? SCANNERS : [scanner]

    try {
      for (const hId of hostIds) {
        for (const sc of scanners) {
          const hostName = hosts.find((h) => h.id === hId)?.name || ''
          const autoName = hostIds.length > 1 || scanners.length > 1
            ? `${name} (${hostName} / ${sc})`
            : name
          await schedulesApi.create({
            host_id: hId,
            name: autoName,
            scanner: sc,
            cron_expression: cron,
          })
        }
      }
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      onClose()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-auto">
        <h2 className="text-xl font-bold text-gray-900 mb-4">{t('schedules.add_title')}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('schedules.name')}</label>
            <input type="text" required value={name} onChange={(e) => setName(e.target.value)} className="input mt-1" />
          </div>

          {/* Host */}
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('schedules.host')}</label>
            <select
              required
              value={hostId}
              onChange={(e) => setHostId(e.target.value === 'all' ? 'all' : Number(e.target.value))}
              className="input mt-1"
            >
              <option value="">{t('scans.select_host')}</option>
              <option value="all">{t('schedules.all_hosts')}</option>
              {hosts.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
            </select>
          </div>

          {/* Scanner */}
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('schedules.scanner')}</label>
            <select value={scanner} onChange={(e) => setScanner(e.target.value)} className="input mt-1">
              <option value="all">{t('schedules.all_scanners')}</option>
              <option value="lynis">Lynis</option>
              <option value="openscap">OpenSCAP</option>
              <option value="trivy">Trivy</option>
              <option value="atomic">Atomic Red Team</option>
            </select>
          </div>

          {/* Frequency */}
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('schedules.frequency')}</label>
            <select value={freq} onChange={(e) => setFreq(e.target.value as Frequency)} className="input mt-1">
              <option value="daily">{t('schedules.freq_daily')}</option>
              <option value="weekly">{t('schedules.freq_weekly')}</option>
              <option value="monthly">{t('schedules.freq_monthly')}</option>
              <option value="yearly">{t('schedules.freq_yearly')}</option>
            </select>
          </div>

          {/* Days of week for daily/weekly */}
          {(freq === 'daily' || freq === 'weekly') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('schedules.days_of_week')}</label>
              <div className="flex gap-1">
                {dayKeys.map(({ key, num }) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => freq === 'weekly' ? setDays([num]) : toggleDay(num)}
                    className={`px-2 py-1 rounded text-xs font-medium border transition-colors ${
                      days.includes(num)
                        ? 'bg-primary-600 text-white border-primary-600'
                        : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
                    }`}
                  >
                    {t(key)}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Day of month for monthly/yearly */}
          {(freq === 'monthly' || freq === 'yearly') && (
            <div>
              <label className="block text-sm font-medium text-gray-700">{t('schedules.day_of_month')}</label>
              <input
                type="number"
                min={1}
                max={28}
                value={dayOfMonth}
                onChange={(e) => setDayOfMonth(Number(e.target.value))}
                className="input mt-1 w-24"
              />
            </div>
          )}

          {/* Month for yearly */}
          {freq === 'yearly' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">{t('schedules.month')}</label>
              <select value={month} onChange={(e) => setMonth(Number(e.target.value))} className="input mt-1 w-32">
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>{i + 1}</option>
                ))}
              </select>
            </div>
          )}

          {/* Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('schedules.time')}</label>
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)} className="input mt-1 w-32" />
          </div>

          {/* Generated cron preview */}
          <div className="text-xs text-gray-400">
            cron: <code className="bg-gray-100 px-1 rounded">{buildCron(freq, time, days, dayOfMonth, month)}</code>
          </div>

          <div className="flex gap-2 pt-4">
            <button type="button" onClick={onClose} className="btn btn-secondary flex-1">{t('common.cancel')}</button>
            <button type="submit" disabled={submitting} className="btn btn-primary flex-1">{t('common.create')}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
