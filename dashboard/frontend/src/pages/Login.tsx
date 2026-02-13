import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { useI18n } from '../lib/i18n'
import { Shield, Loader2, KeyRound } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const [showChangePassword, setShowChangePassword] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const { login, changePassword } = useAuthStore()
  const { t } = useI18n()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password)
      const state = useAuthStore.getState()
      if (state.mustChangePassword) {
        setCurrentPassword(password)
        setShowChangePassword(true)
      } else {
        navigate('/')
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || t('auth.invalid_creds'))
      } else {
        setError(t('auth.invalid_creds'))
      }
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (newPassword !== confirmPassword) {
      setError(t('auth.pwd_mismatch'))
      return
    }
    if (newPassword.length < 8) {
      setError(t('auth.pwd_short'))
      return
    }

    setLoading(true)
    try {
      await changePassword(currentPassword, newPassword)
      navigate('/')
    } catch {
      setError(t('auth.change_failed'))
    } finally {
      setLoading(false)
    }
  }

  if (showChangePassword) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="flex justify-center">
              <KeyRound className="h-16 w-16 text-warning-500" />
            </div>
            <h2 className="mt-6 text-3xl font-bold text-gray-900">{t('auth.change_password')}</h2>
            <p className="mt-2 text-sm text-gray-600">
              {t('auth.change_pwd_desc')}
            </p>
          </div>

          <form className="mt-8 space-y-6" onSubmit={handleChangePassword}>
            {error && (
              <div className="bg-danger-50 border border-danger-500 text-danger-600 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="new-password" className="block text-sm font-medium text-gray-700">
                  {t('auth.new_password')}
                </label>
                <input
                  id="new-password"
                  type="password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input mt-1"
                  placeholder="Enter new password (min 8 chars)"
                />
              </div>

              <div>
                <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700">
                  {t('auth.confirm_password')}
                </label>
                <input
                  id="confirm-password"
                  type="password"
                  required
                  minLength={8}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input mt-1"
                  placeholder="Confirm new password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  {t('auth.changing')}
                </>
              ) : (
                t('auth.change_continue')
              )}
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center">
            <Shield className="h-16 w-16 text-primary-600" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">{t('auth.title')}</h2>
          <p className="mt-2 text-sm text-gray-600">
            {t('auth.subtitle')}
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-danger-50 border border-danger-500 text-danger-600 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                {t('auth.username')}
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input mt-1"
                placeholder="Enter your username"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                {t('auth.password')}
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input mt-1"
                placeholder="Enter your password"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary w-full"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                {t('auth.signing_in')}
              </>
            ) : (
              t('auth.sign_in')
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
