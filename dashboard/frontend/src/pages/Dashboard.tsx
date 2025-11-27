import { useQuery } from '@tanstack/react-query'
import { hostsApi, scansApi } from '../lib/api'
import {
  Server,
  Scan,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface Host {
  id: number
  name: string
  status: string
  last_scan_score: number | null
}

interface Scan {
  id: number
  host_id: number
  host_name: string
  scanner: string
  status: string
  score: number | null
  started_at: string
  completed_at: string
}

export default function Dashboard() {
  const { data: hosts = [] } = useQuery<Host[]>({
    queryKey: ['hosts'],
    queryFn: async () => {
      const res = await hostsApi.getAll()
      return res.data
    },
  })

  const { data: recentScans = [] } = useQuery<Scan[]>({
    queryKey: ['scans', 'recent'],
    queryFn: async () => {
      const res = await scansApi.getAll({ limit: 10 })
      return res.data
    },
  })

  const stats = {
    totalHosts: hosts.length,
    onlineHosts: hosts.filter((h) => h.status === 'online').length,
    totalScans: recentScans.length,
    avgScore: Math.round(
      recentScans.filter((s) => s.score !== null).reduce((acc, s) => acc + (s.score || 0), 0) /
        (recentScans.filter((s) => s.score !== null).length || 1)
    ),
  }

  // Mock chart data
  const chartData = [
    { date: 'Mon', score: 72 },
    { date: 'Tue', score: 75 },
    { date: 'Wed', score: 78 },
    { date: 'Thu', score: 74 },
    { date: 'Fri', score: 80 },
    { date: 'Sat', score: 82 },
    { date: 'Sun', score: 85 },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">Security hardening overview</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Hosts"
          value={stats.totalHosts}
          icon={Server}
          color="primary"
        />
        <StatCard
          title="Online Hosts"
          value={stats.onlineHosts}
          icon={CheckCircle}
          color="success"
        />
        <StatCard
          title="Recent Scans"
          value={stats.totalScans}
          icon={Scan}
          color="warning"
        />
        <StatCard
          title="Avg Score"
          value={`${stats.avgScore}%`}
          icon={TrendingUp}
          color="primary"
        />
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Score Trend Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Score Trend</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#0ea5e9"
                  fill="#0ea5e9"
                  fillOpacity={0.2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Scans */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Scans</h3>
          <div className="space-y-3">
            {recentScans.slice(0, 5).map((scan) => (
              <div
                key={scan.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <StatusIcon status={scan.status} />
                  <div>
                    <p className="font-medium text-gray-900">{scan.host_name}</p>
                    <p className="text-sm text-gray-500">{scan.scanner}</p>
                  </div>
                </div>
                <div className="text-right">
                  {scan.score !== null && (
                    <p className="font-semibold text-gray-900">{scan.score}%</p>
                  )}
                  <p className="text-xs text-gray-500">
                    {scan.completed_at
                      ? new Date(scan.completed_at).toLocaleString()
                      : 'In progress'}
                  </p>
                </div>
              </div>
            ))}
            {recentScans.length === 0 && (
              <p className="text-gray-500 text-center py-4">No recent scans</p>
            )}
          </div>
        </div>
      </div>

      {/* Host Status */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Host Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {hosts.map((host) => (
            <div
              key={host.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div
                  className={`h-3 w-3 rounded-full ${
                    host.status === 'online'
                      ? 'bg-success-500'
                      : host.status === 'scanning'
                      ? 'bg-warning-500 animate-pulse'
                      : 'bg-gray-400'
                  }`}
                />
                <span className="font-medium text-gray-900">{host.name}</span>
              </div>
              {host.last_scan_score !== null && (
                <span
                  className={`badge ${
                    host.last_scan_score >= 80
                      ? 'badge-success'
                      : host.last_scan_score >= 60
                      ? 'badge-warning'
                      : 'badge-danger'
                  }`}
                >
                  {host.last_scan_score}%
                </span>
              )}
            </div>
          ))}
          {hosts.length === 0 && (
            <p className="text-gray-500 col-span-full text-center py-4">
              No hosts configured
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string
  value: string | number
  icon: React.ComponentType<{ className?: string }>
  color: 'primary' | 'success' | 'warning' | 'danger'
}) {
  const colors = {
    primary: 'bg-primary-50 text-primary-600',
    success: 'bg-success-50 text-success-600',
    warning: 'bg-warning-50 text-warning-600',
    danger: 'bg-danger-50 text-danger-600',
  }

  return (
    <div className="card">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
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
