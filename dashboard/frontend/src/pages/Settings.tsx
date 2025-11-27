import { useAuthStore } from '../store/auth'
import { User, Shield, Bell, Database } from 'lucide-react'

export default function Settings() {
  const { user } = useAuthStore()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500">Manage your account and preferences</p>
      </div>

      <div className="grid gap-6">
        {/* Profile */}
        <div className="card">
          <div className="flex items-center gap-4 mb-4">
            <User className="h-6 w-6 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">Profile</h2>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Username</label>
              <p className="text-gray-900">{user?.username}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Email</label>
              <p className="text-gray-900">{user?.email}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Role</label>
              <p className="text-gray-900 capitalize">{user?.role}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Status</label>
              <span className={`badge ${user?.is_active ? 'badge-success' : 'badge-danger'}`}>
                {user?.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>

        {/* Security */}
        <div className="card">
          <div className="flex items-center gap-4 mb-4">
            <Shield className="h-6 w-6 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">Security</h2>
          </div>
          <div className="space-y-4">
            <button className="btn btn-secondary">Change Password</button>
            <p className="text-sm text-gray-500">
              Last password change: Never
            </p>
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <div className="flex items-center gap-4 mb-4">
            <Bell className="h-6 w-6 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">Notifications</h2>
          </div>
          <div className="space-y-3">
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="rounded border-gray-300" />
              <span className="text-gray-700">Email notifications for scan completion</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="rounded border-gray-300" />
              <span className="text-gray-700">Email notifications for scan failures</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" className="rounded border-gray-300" />
              <span className="text-gray-700">Weekly security digest</span>
            </label>
          </div>
        </div>

        {/* System Info */}
        <div className="card">
          <div className="flex items-center gap-4 mb-4">
            <Database className="h-6 w-6 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">System</h2>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <label className="block text-gray-500">Version</label>
              <p className="text-gray-900">1.0.0</p>
            </div>
            <div>
              <label className="block text-gray-500">API Endpoint</label>
              <p className="text-gray-900">/api/v1</p>
            </div>
            <div>
              <label className="block text-gray-500">Prometheus</label>
              <a href="http://localhost:9090" target="_blank" className="text-primary-600 hover:underline">
                localhost:9090
              </a>
            </div>
            <div>
              <label className="block text-gray-500">Grafana</label>
              <a href="http://localhost:3000" target="_blank" className="text-primary-600 hover:underline">
                localhost:3000
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
