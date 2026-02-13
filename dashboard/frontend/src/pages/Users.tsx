import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi, CreateUserData } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { useI18n } from '../lib/i18n'
import {
  UserPlus,
  Trash2,
  Shield,
  ShieldCheck,
  Eye,
  ToggleLeft,
  ToggleRight,
  Loader2,
  X,
} from 'lucide-react'

interface UserItem {
  id: number
  username: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  is_superuser: boolean
  must_change_password: boolean
  created_at: string
}

const ROLE_STYLES: Record<string, string> = {
  admin: 'bg-danger-50 text-danger-600',
  user: 'bg-primary-50 text-primary-600',
  auditor: 'bg-warning-50 text-warning-600',
  viewer: 'bg-gray-100 text-gray-500',
}

const ROLE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  admin: ShieldCheck,
  user: Shield,
  auditor: Eye,
}

export default function Users() {
  const currentUser = useAuthStore((s) => s.user)
  const queryClient = useQueryClient()
  const { t, lang } = useI18n()
  const [showCreate, setShowCreate] = useState(false)
  const [error, setError] = useState('')

  const { data: users = [], isLoading } = useQuery<UserItem[]>({
    queryKey: ['users'],
    queryFn: async () => {
      const res = await usersApi.getAll()
      return res.data
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => usersApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const roleMutation = useMutation({
    mutationFn: ({ id, role }: { id: number; role: string }) => usersApi.updateRole(id, role),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const toggleMutation = useMutation({
    mutationFn: (id: number) => usersApi.toggleActive(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const isAdmin = currentUser?.role === 'admin' || currentUser?.is_superuser

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        {t('users.admin_required')}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('users.title')}</h1>
          <p className="text-gray-500">{t('users.subtitle')}</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <UserPlus className="h-4 w-4 mr-2" />
          {t('users.create')}
        </button>
      </div>

      {error && (
        <div className="bg-danger-50 border border-danger-500 text-danger-600 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b bg-gray-50">
                <th className="px-4 py-3 font-medium">{t('users.username')}</th>
                <th className="px-4 py-3 font-medium">{t('users.email')}</th>
                <th className="px-4 py-3 font-medium">{t('users.role')}</th>
                <th className="px-4 py-3 font-medium">{t('table.status')}</th>
                <th className="px-4 py-3 font-medium">{t('users.created')}</th>
                <th className="px-4 py-3 font-medium text-right">{t('table.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((u) => {
                const RoleIcon = ROLE_ICONS[u.role] || Shield
                return (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-gray-900">{u.username}</p>
                        {u.full_name && (
                          <p className="text-xs text-gray-400">{u.full_name}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{u.email}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${ROLE_STYLES[u.role] || ROLE_STYLES.viewer}`}>
                          <RoleIcon className="h-3 w-3" />
                          {u.role}
                        </span>
                        {u.id !== currentUser?.id && (
                          <select
                            value={u.role}
                            onChange={(e) => roleMutation.mutate({ id: u.id, role: e.target.value })}
                            className="text-xs border border-gray-200 rounded px-1 py-0.5"
                          >
                            <option value="admin">admin</option>
                            <option value="user">user</option>
                            <option value="auditor">auditor</option>
                          </select>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${u.is_active ? 'bg-success-50 text-success-600' : 'bg-gray-100 text-gray-500'}`}>
                          {u.is_active ? t('users.active') : t('users.disabled')}
                        </span>
                        {u.must_change_password && (
                          <span className="text-xs text-warning-500">{t('users.pwd_change')}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(u.created_at).toLocaleDateString(lang === 'ru' ? 'ru-RU' : 'en-US')}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {u.id !== currentUser?.id && (
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => toggleMutation.mutate(u.id)}
                            className="p-1 rounded hover:bg-gray-100"
                            title={u.is_active ? t('users.disabled') : t('users.active')}
                          >
                            {u.is_active ? (
                              <ToggleRight className="h-4 w-4 text-success-500" />
                            ) : (
                              <ToggleLeft className="h-4 w-4 text-gray-400" />
                            )}
                          </button>
                          <button
                            onClick={() => {
                              if (confirm(`${t('users.delete_confirm')} "${u.username}"?`)) {
                                deleteMutation.mutate(u.id)
                              }
                            }}
                            className="p-1 rounded hover:bg-danger-50"
                            title="Delete user"
                          >
                            <Trash2 className="h-4 w-4 text-danger-500" />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {users.length === 0 && (
            <div className="text-center py-8 text-gray-400">{t('users.no_users')}</div>
          )}
        </div>
      )}

      {showCreate && (
        <CreateUserModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false)
            queryClient.invalidateQueries({ queryKey: ['users'] })
          }}
          onError={setError}
        />
      )}
    </div>
  )
}

function CreateUserModal({
  onClose,
  onCreated,
  onError,
}: {
  onClose: () => void
  onCreated: () => void
  onError: (msg: string) => void
}) {
  const [form, setForm] = useState<CreateUserData>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'user',
  })
  const [loading, setLoading] = useState(false)
  const { t } = useI18n()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    onError('')
    try {
      await usersApi.create(form)
      onCreated()
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to create user'
      onError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900">{t('users.create_title')}</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-gray-100">
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('users.username')}</label>
            <input
              type="text"
              required
              minLength={3}
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              className="input mt-1"
              placeholder="username"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">{t('users.email')}</label>
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="input mt-1"
              placeholder="user@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">{t('users.full_name')}</label>
            <input
              type="text"
              value={form.full_name || ''}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="input mt-1"
              placeholder="Full Name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">{t('users.password')}</label>
            <input
              type="password"
              required
              minLength={8}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="input mt-1"
              placeholder="Min 8 characters"
            />
            <p className="text-xs text-gray-400 mt-1">{t('users.pwd_hint')}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">{t('users.role')}</label>
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as CreateUserData['role'] })}
              className="input mt-1"
            >
              <option value="admin">{t('users.role_admin')}</option>
              <option value="user">{t('users.role_user')}</option>
              <option value="auditor">{t('users.role_auditor')}</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              {t('common.cancel')}
            </button>
            <button type="submit" disabled={loading} className="btn btn-primary">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  {t('common.loading')}
                </>
              ) : (
                t('users.create')
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
