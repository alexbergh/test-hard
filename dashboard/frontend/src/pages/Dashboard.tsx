import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../lib/api'
import {
  Server,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Activity,
  Calendar,
  Bug,
  RefreshCw,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useState } from 'react'
import { useI18n } from '../lib/i18n'

interface DashboardStats {
  hostname: string
  summary: {
    total_hosts: number
    online_hosts: number
    offline_hosts: number
    scanning_hosts: number
    total_scans: number
    avg_score: number
    avg_duration: number
    active_schedules: number
    total_findings: number
    failed_findings: number
  }
  score_distribution: Record<string, number>
  scans_by_status: Record<string, number>
  scans_by_scanner: Record<string, number>
  score_trend: Array<{ date: string; avg_score: number; scan_count: number }>
  scanner_comparison: Array<{
    scanner: string
    avg_score: number
    total_passed: number
    total_failed: number
    total_warnings: number
    total_scans: number
  }>
  findings_by_severity: Record<string, number>
  findings_by_status: Record<string, number>
  top_failing_rules: Array<{
    rule_id: string
    title: string
    severity: string
    category: string | null
    scanner: string
    count: number
  }>
  host_scores: Array<{
    id: number
    name: string
    status: string
    os_family: string | null
    host_type: string
    score: number | null
    tags: string[]
  }>
  recent_scans: Array<{
    id: number
    host_name: string
    scanner: string
    status: string
    score: number | null
    started_at: string | null
    completed_at: string | null
    duration_seconds: number | null
    passed: number
    failed: number
    warnings: number
  }>
  upcoming_scans: Array<{
    id: number
    name: string
    host_name: string
    scanner: string
    next_run_at: string
    cron_expression: string
    run_count: number
  }>
  scan_activity: Array<{ date: string; count: number }>
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#dc2626',
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#0ea5e9',
  info: '#6b7280',
}

const STATUS_COLORS: Record<string, string> = {
  completed: '#22c55e',
  failed: '#ef4444',
  running: '#f59e0b',
  pending: '#6b7280',
  cancelled: '#9ca3af',
}

const SCORE_DIST_COLORS: Record<string, string> = {
  critical: '#dc2626',
  low: '#f59e0b',
  medium: '#0ea5e9',
  good: '#22c55e',
  excellent: '#16a34a',
}

const SCORE_DIST_LABELS: Record<string, string> = {
  critical: '< 40',
  low: '40–59',
  medium: '60–79',
  good: '80–94',
  excellent: '95–100',
}

const PERIOD_KEYS = ['1h', '12h', '24h', '7d', '14d', '30d', '90d'] as const
const PERIOD_PARAMS: Record<string, { hours?: number; days?: number }> = {
  '1h': { hours: 1 },
  '12h': { hours: 12 },
  '24h': { hours: 24 },
  '7d': { days: 7 },
  '14d': { days: 14 },
  '30d': { days: 30 },
  '90d': { days: 90 },
}

export default function Dashboard() {
  const [periodKey, setPeriodKey] = useState('30d')
  const [scannerFilter, setScannerFilter] = useState('all')
  const { t } = useI18n()

  const { data, isLoading, error } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats', periodKey],
    queryFn: async () => {
      const res = await dashboardApi.getStats(PERIOD_PARAMS[periodKey] || { days: 30 })
      return res.data
    },
    refetchInterval: 30000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-64 text-danger-500">
        <AlertTriangle className="h-6 w-6 mr-2" />
        <span>{t('dashboard.failed_load')}</span>
      </div>
    )
  }

  const { summary } = data

  // Prepare chart data
  const severityData = Object.entries(data.findings_by_severity)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({ name: key, value }))

  const scanStatusData = Object.entries(data.scans_by_status)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({ name: key, value }))

  const scoreDistData = Object.entries(data.score_distribution)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({
      name: SCORE_DIST_LABELS[key] || key,
      value,
      key,
    }))

  const scannerBarData = data.scanner_comparison.map((s) => ({
    scanner: s.scanner,
    'Avg Score': s.avg_score,
    Passed: s.total_passed,
    Failed: s.total_failed,
    Warnings: s.total_warnings,
  }))

  const filteredRules = scannerFilter === 'all'
    ? data.top_failing_rules
    : data.top_failing_rules.filter((r) => r.scanner === scannerFilter)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.title')}</h1>
          <p className="text-gray-500">
            {data.hostname && (
              <span className="inline-flex items-center gap-1 mr-2 font-medium text-gray-700">
                <Server className="h-3.5 w-3.5" />
                {data.hostname}
              </span>
            )}
            {t('dashboard.subtitle')}
          </p>
        </div>
        <select
          value={periodKey}
          onChange={(e) => setPeriodKey(e.target.value)}
          className="input w-auto"
        >
          {PERIOD_KEYS.map((key) => (
            <option key={key} value={key}>
              {t(`period.${key}`)}
            </option>
          ))}
        </select>
      </div>

      {/* KPI Cards - Row 1 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard title={t('dashboard.hosts')} value={summary.total_hosts} icon={Server} color="primary" />
        <StatCard title={t('dashboard.online')} value={summary.online_hosts} icon={CheckCircle} color="success" />
        <StatCard title={t('dashboard.scans')} value={summary.total_scans} icon={Activity} color="primary" subtitle={t(`period.${periodKey}`)} />
        <StatCard
          title={t('dashboard.avg_score')}
          value={`${summary.avg_score}%`}
          icon={TrendingUp}
          color={summary.avg_score >= 80 ? 'success' : summary.avg_score >= 60 ? 'warning' : 'danger'}
        />
        <StatCard title={t('dashboard.findings')} value={summary.failed_findings} icon={Bug} color="danger" subtitle={t('dashboard.findings_failed')} />
        <StatCard title={t('dashboard.schedules')} value={summary.active_schedules} icon={Calendar} color="primary" subtitle={t('dashboard.schedules_active')} />
      </div>

      {/* Row 2: Score Trend + Severity Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score Trend */}
        <div className="card lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.score_trend')}</h3>
          <div className="h-64">
            {data.score_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.score_trend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(v) => {
                      const d = new Date(v)
                      return `${d.getDate()}.${d.getMonth() + 1}`
                    }}
                    fontSize={12}
                  />
                  <YAxis domain={[0, 100]} fontSize={12} />
                  <Tooltip
                    labelFormatter={(v) => new Date(v).toLocaleDateString('ru-RU')}
                    formatter={(value: number, name: string) => [
                      name === 'avg_score' ? `${value}%` : value,
                      name === 'avg_score' ? 'Avg Score' : 'Scans',
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="avg_score"
                    stroke="#0ea5e9"
                    fill="#0ea5e9"
                    fillOpacity={0.15}
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="scan_count"
                    stroke="#22c55e"
                    fill="#22c55e"
                    fillOpacity={0.1}
                    strokeWidth={1}
                    yAxisId={0}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message={t('dashboard.no_scan_data')} />
            )}
          </div>
        </div>

        {/* Findings by Severity (Pie) */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.findings_by_severity')}</h3>
          <div className="h-64">
            {severityData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                    fontSize={11}
                  >
                    {severityData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={SEVERITY_COLORS[entry.name] || '#6b7280'}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message={t('dashboard.no_findings')} />
            )}
          </div>
        </div>
      </div>

      {/* Row 3: Scanner Comparison + Scan Status + Score Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scanner Comparison */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.scanner_comparison')}</h3>
          <div className="h-64">
            {scannerBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={scannerBarData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} fontSize={12} />
                  <YAxis type="category" dataKey="scanner" fontSize={12} width={70} />
                  <Tooltip />
                  <Bar dataKey="Avg Score" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message={t('dashboard.no_scanner')} />
            )}
          </div>
        </div>

        {/* Scans by Status (Pie) */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.scans_by_status')}</h3>
          <div className="h-64">
            {scanStatusData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={scanStatusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                    labelLine={false}
                    fontSize={11}
                  >
                    {scanStatusData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={STATUS_COLORS[entry.name] || '#6b7280'}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message={t('dashboard.no_status')} />
            )}
          </div>
        </div>

        {/* Score Distribution */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.host_score_dist')}</h3>
          <div className="h-64">
            {scoreDistData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={scoreDistData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={11} />
                  <YAxis allowDecimals={false} fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="value" name="Hosts" radius={[4, 4, 0, 0]}>
                    {scoreDistData.map((entry) => (
                      <Cell
                        key={entry.key}
                        fill={SCORE_DIST_COLORS[entry.key] || '#6b7280'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message={t('dashboard.no_score')} />
            )}
          </div>
        </div>
      </div>

      {/* Row 4: Host Compliance Table + Recent Scans */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Host Compliance */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.host_compliance')}</h3>
          <div className="overflow-auto max-h-80">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 font-medium">{t('table.host')}</th>
                  <th className="pb-2 font-medium">{t('table.type')}</th>
                  <th className="pb-2 font-medium">{t('table.os')}</th>
                  <th className="pb-2 font-medium text-right">{t('table.score')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.host_scores.map((host) => (
                  <tr key={host.id} className="hover:bg-gray-50">
                    <td className="py-2">
                      <div className="flex items-center gap-2">
                        <div
                          className={`h-2 w-2 rounded-full ${
                            host.status === 'online'
                              ? 'bg-success-500'
                              : host.status === 'scanning'
                              ? 'bg-warning-500 animate-pulse'
                              : 'bg-gray-400'
                          }`}
                        />
                        <span className="font-medium text-gray-900">{host.name}</span>
                      </div>
                    </td>
                    <td className="py-2 text-gray-500">{host.host_type}</td>
                    <td className="py-2 text-gray-500">{host.os_family || '—'}</td>
                    <td className="py-2 text-right">
                      {host.score !== null ? (
                        <ScoreBadge score={host.score} />
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.host_scores.length === 0 && (
              <EmptyState message={t('dashboard.no_hosts')} />
            )}
          </div>
        </div>

        {/* Recent Scans */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.recent_scans')}</h3>
          <div className="space-y-3 max-h-80 overflow-auto">
            {data.recent_scans.map((scan) => (
              <div
                key={scan.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <StatusIcon status={scan.status} />
                  <div>
                    <p className="font-medium text-gray-900">{scan.host_name}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span className="badge badge-info">{scan.scanner}</span>
                      {scan.duration_seconds !== null && (
                        <span>{formatDuration(scan.duration_seconds)}</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  {scan.score !== null && <ScoreBadge score={scan.score} />}
                  <p className="text-xs text-gray-500 mt-1">
                    {scan.completed_at
                      ? new Date(scan.completed_at).toLocaleString('ru-RU', {
                          day: '2-digit',
                          month: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                        })
                      : t('common.in_progress')}
                  </p>
                </div>
              </div>
            ))}
            {data.recent_scans.length === 0 && (
              <EmptyState message={t('dashboard.no_scans')} />
            )}
          </div>
        </div>
      </div>

      {/* Row 5: Top Failing Rules + Upcoming Schedules */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Failing Rules */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{t('dashboard.top_failing')}</h3>
            <select
              value={scannerFilter}
              onChange={(e) => setScannerFilter(e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-2 py-1 bg-white text-gray-700"
            >
              <option value="all">{t('dashboard.all_scanners')}</option>
              <option value="lynis">Lynis</option>
              <option value="openscap">OpenSCAP</option>
              <option value="trivy">Trivy</option>
              <option value="atomic">Atomic Red Team</option>
            </select>
          </div>
          <div className="overflow-auto max-h-80 pr-2">
            {filteredRules.length > 0 ? (
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white z-10">
                  <tr className="text-left text-gray-500 border-b">
                    <th className="pb-2 font-medium">{t('table.rule')}</th>
                    <th className="pb-2 font-medium">{t('table.scanner')}</th>
                    <th className="pb-2 font-medium">{t('table.severity')}</th>
                    <th className="pb-2 font-medium text-right pr-1">{t('table.hits')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredRules.map((rule, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="py-2">
                        <p className="font-medium text-gray-900 truncate max-w-xs" title={rule.title}>
                          {rule.title}
                        </p>
                        <p className="text-xs text-gray-400">{rule.rule_id}</p>
                      </td>
                      <td className="py-2">
                        <ScannerBadge scanner={rule.scanner} />
                      </td>
                      <td className="py-2">
                        <SeverityBadge severity={rule.severity} />
                      </td>
                      <td className="py-2 text-right font-semibold text-gray-700">{rule.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <EmptyState message={t('dashboard.no_rules')} />
            )}
          </div>
        </div>

        {/* Upcoming Schedules */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.upcoming_scans')}</h3>
          <div className="space-y-3 max-h-80 overflow-auto">
            {data.upcoming_scans.map((sched) => (
              <div
                key={sched.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-primary-500" />
                  <div>
                    <p className="font-medium text-gray-900">{sched.name}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span>{sched.host_name}</span>
                      <span className="badge badge-info">{sched.scanner}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-700">
                    {new Date(sched.next_run_at).toLocaleString('ru-RU', {
                      day: '2-digit',
                      month: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                  <p className="text-xs text-gray-400">
                    runs: {sched.run_count} | {sched.cron_expression}
                  </p>
                </div>
              </div>
            ))}
            {data.upcoming_scans.length === 0 && (
              <EmptyState message={t('dashboard.no_upcoming')} />
            )}
          </div>
        </div>
      </div>

      {/* Row 6: Scan Activity Heatmap (bar chart) */}
      {data.scan_activity.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.scan_activity')}</h3>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.scan_activity}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={(v) => {
                    const d = new Date(v)
                    return `${d.getDate()}.${d.getMonth() + 1}`
                  }}
                  fontSize={11}
                />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip
                  labelFormatter={(v) => new Date(v).toLocaleDateString('ru-RU')}
                />
                <Bar dataKey="count" name="Scans" fill="#0ea5e9" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}

/* ============ Helper Components ============ */

function StatCard({
  title,
  value,
  icon: Icon,
  color,
  subtitle,
}: {
  title: string
  value: string | number
  icon: React.ComponentType<{ className?: string }>
  color: 'primary' | 'success' | 'warning' | 'danger'
  subtitle?: string
}) {
  const colors = {
    primary: 'bg-primary-50 text-primary-600',
    success: 'bg-success-50 text-success-600',
    warning: 'bg-warning-50 text-warning-600',
    danger: 'bg-danger-50 text-danger-600',
  }

  return (
    <div className="card !p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="text-xs text-gray-500 truncate">
            {title}
            {subtitle && <span className="ml-1 text-gray-400">({subtitle})</span>}
          </p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-5 w-5 text-success-500" />
    case 'failed':
      return <XCircle className="h-5 w-5 text-danger-500" />
    case 'running':
      return <Clock className="h-5 w-5 text-warning-500 animate-spin" />
    default:
      return <AlertTriangle className="h-5 w-5 text-gray-400" />
  }
}

function ScoreBadge({ score }: { score: number }) {
  const cls =
    score >= 80
      ? 'badge-success'
      : score >= 60
      ? 'badge-warning'
      : 'badge-danger'
  return <span className={`badge ${cls}`}>{score}%</span>
}

function ScannerBadge({ scanner }: { scanner: string }) {
  const cls: Record<string, string> = {
    lynis: 'bg-blue-50 text-blue-700',
    openscap: 'bg-emerald-50 text-emerald-700',
    trivy: 'bg-violet-50 text-violet-700',
    atomic: 'bg-orange-50 text-orange-700',
  }
  const labels: Record<string, string> = {
    lynis: 'Lynis',
    openscap: 'OpenSCAP',
    trivy: 'Trivy',
    atomic: 'Atomic',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls[scanner] || 'bg-gray-100 text-gray-600'}`}>
      {labels[scanner] || scanner}
    </span>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const cls: Record<string, string> = {
    critical: 'bg-danger-50 text-danger-600',
    high: 'bg-danger-50 text-danger-500',
    medium: 'bg-warning-50 text-warning-600',
    low: 'bg-primary-50 text-primary-600',
    info: 'bg-gray-100 text-gray-500',
  }
  return (
    <span className={`badge ${cls[severity.toLowerCase()] || cls.info}`}>
      {severity}
    </span>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
      {message}
    </div>
  )
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s > 0 ? `${m}m ${s}s` : `${m}m`
}
