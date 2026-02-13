import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { useI18n } from '../lib/i18n'
import {
  LayoutDashboard,
  Server,
  Scan,
  Calendar,
  Settings,
  Users,
  LogOut,
  Shield,
  Menu,
  X,
  Globe,
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

const navigation = [
  { nameKey: 'nav.dashboard', href: '/', icon: LayoutDashboard },
  { nameKey: 'nav.hosts', href: '/hosts', icon: Server },
  { nameKey: 'nav.scans', href: '/scans', icon: Scan },
  { nameKey: 'nav.schedules', href: '/schedules', icon: Calendar },
  { nameKey: 'nav.settings', href: '/settings', icon: Settings },
  { nameKey: 'nav.users', href: '/users', icon: Users, adminOnly: true },
] as const

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout } = useAuthStore()
  const { t, lang, setLang } = useI18n()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 transform transition-transform duration-300 ease-in-out lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center justify-between px-4">
            <div className="flex items-center gap-2">
              <Shield className="h-8 w-8 text-primary-500" />
              <span className="text-xl font-bold text-white">Test-Hard</span>
            </div>
            <button
              className="lg:hidden text-gray-400 hover:text-white"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.filter((item) => !('adminOnly' in item && item.adminOnly) || user?.role === 'admin' || user?.is_superuser).map((item) => (
              <NavLink
                key={item.nameKey}
                to={item.href}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  )
                }
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="h-5 w-5" />
                {t(item.nameKey)}
              </NavLink>
            ))}
          </nav>

          {/* User section */}
          <div className="border-t border-gray-800 p-4">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center">
                <span className="text-sm font-medium text-white">
                  {user?.username?.[0]?.toUpperCase() || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {user?.username || 'User'}
                </p>
                <p className="text-xs text-gray-400 truncate">{user?.role || 'viewer'}</p>
              </div>
              <button
                onClick={handleLogout}
                className="text-gray-400 hover:text-white"
                title="Logout"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-gray-200 bg-white px-4 lg:px-6">
          <button
            className="lg:hidden text-gray-500 hover:text-gray-700"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-4">
            <button
              onClick={() => setLang(lang === 'ru' ? 'en' : 'ru')}
              className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-500 hover:text-gray-700 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
              title={lang === 'ru' ? 'Switch to English' : 'Переключить на русский'}
            >
              <Globe className="h-3.5 w-3.5" />
              {lang === 'ru' ? 'RU' : 'EN'}
            </button>
            <span className="text-sm text-gray-500">
              {new Date().toLocaleDateString(lang === 'ru' ? 'ru-RU' : 'en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </span>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
