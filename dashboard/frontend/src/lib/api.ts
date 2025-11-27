import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const storage = localStorage.getItem('auth-storage')
  if (storage) {
    try {
      const { state } = JSON.parse(storage)
      if (state?.token) {
        config.headers.Authorization = `Bearer ${state.token}`
      }
    } catch {
      // Invalid storage
    }
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API functions
export const hostsApi = {
  getAll: () => api.get('/hosts'),
  getById: (id: number) => api.get(`/hosts/${id}`),
  create: (data: CreateHostData) => api.post('/hosts', data),
  update: (id: number, data: UpdateHostData) => api.patch(`/hosts/${id}`, data),
  delete: (id: number) => api.delete(`/hosts/${id}`),
  checkStatus: (id: number) => api.post(`/hosts/${id}/check-status`),
  syncDocker: () => api.post('/hosts/sync-docker'),
}

export const scansApi = {
  getAll: (params?: ScanFilters) => api.get('/scans', { params }),
  getById: (id: number, includeResults = false) =>
    api.get(`/scans/${id}`, { params: { include_results: includeResults } }),
  create: (data: CreateScanData) => api.post('/scans', data),
  start: (id: number) => api.post(`/scans/${id}/start`),
  cancel: (id: number) => api.post(`/scans/${id}/cancel`),
}

export const schedulesApi = {
  getAll: (params?: ScheduleFilters) => api.get('/schedules', { params }),
  getById: (id: number) => api.get(`/schedules/${id}`),
  create: (data: CreateScheduleData) => api.post('/schedules', data),
  update: (id: number, data: UpdateScheduleData) => api.patch(`/schedules/${id}`, data),
  delete: (id: number) => api.delete(`/schedules/${id}`),
  toggle: (id: number) => api.post(`/schedules/${id}/toggle`),
  getJobs: () => api.get('/schedules/jobs/status'),
}

// Types
export interface CreateHostData {
  name: string
  display_name?: string
  description?: string
  host_type: 'container' | 'ssh' | 'local'
  address?: string
  port?: number
  ssh_user?: string
  os_family?: string
  enabled_scanners?: Record<string, boolean>
  tags?: string[]
}

export interface UpdateHostData {
  display_name?: string
  description?: string
  address?: string
  port?: number
  is_active?: boolean
  enabled_scanners?: Record<string, boolean>
  tags?: string[]
}

export interface CreateScanData {
  host_id: number
  scanner: 'lynis' | 'openscap' | 'trivy' | 'atomic'
  profile?: string
}

export interface ScanFilters {
  host_id?: number
  scanner?: string
  status?: string
  limit?: number
  offset?: number
}

export interface CreateScheduleData {
  host_id: number
  name: string
  description?: string
  scanner: string
  profile?: string
  cron_expression: string
  timezone?: string
  notify_on_completion?: boolean
  notify_on_failure?: boolean
  notification_channels?: string[]
}

export interface UpdateScheduleData {
  name?: string
  description?: string
  cron_expression?: string
  is_active?: boolean
}

export interface ScheduleFilters {
  host_id?: number
  active_only?: boolean
}
