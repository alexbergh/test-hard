import { useState } from 'react'
import { useAuthStore } from '../store/auth'
import { useI18n } from '../lib/i18n'
import { api } from '../lib/api'
import { User, Shield, Bell, Database, Loader2, CheckCircle, Edit2 } from 'lucide-react'

export default function Settings() {
  const { user, changePassword, fetchUser } = useAuthStore()
  const { t } = useI18n()

  // Email editing
  const [editingEmail, setEditingEmail] = useState(false)
  const [newEmail, setNewEmail] = useState('')
  const [emailLoading, setEmailLoading] = useState(false)
  const [emailMsg, setEmailMsg] = useState('')

  // Notification email
  const [notifEmail, setNotifEmail] = useState('')
  const [notifLoading, setNotifLoading] = useState(false)
  const [notifMsg, setNotifMsg] = useState('')
  const [notifLoaded, setNotifLoaded] = useState(false)

  // Password change
  const [showPwdForm, setShowPwdForm] = useState(false)
  const [currentPwd, setCurrentPwd] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [confirmPwd, setConfirmPwd] = useState('')
  const [pwdLoading, setPwdLoading] = useState(false)
  const [pwdMsg, setPwdMsg] = useState('')
  const [pwdError, setPwdError] = useState('')

  const handleEmailSave = async () => {
    setEmailMsg('')
    if (!newEmail.trim() || !newEmail.includes('@')) return
    setEmailLoading(true)
    try {
      await api.patch('/auth/me/email', { email: newEmail.trim() })
      await fetchUser()
      setEditingEmail(false)
      setNewEmail('')
      setEmailMsg(t('settings.email_saved'))
      setTimeout(() => setEmailMsg(''), 3000)
    } catch {
      setEmailMsg(t('settings.email_error'))
    } finally {
      setEmailLoading(false)
    }
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setPwdError('')
    setPwdMsg('')

    if (newPwd !== confirmPwd) {
      setPwdError(t('settings.pwd_mismatch'))
      return
    }
    if (newPwd.length < 8) {
      setPwdError(t('settings.pwd_short'))
      return
    }

    setPwdLoading(true)
    try {
      await changePassword(currentPwd, newPwd)
      await fetchUser()
      setPwdMsg(t('settings.pwd_changed'))
      setShowPwdForm(false)
      setCurrentPwd('')
      setNewPwd('')
      setConfirmPwd('')
      setTimeout(() => setPwdMsg(''), 3000)
    } catch {
      setPwdError(t('settings.pwd_error'))
    } finally {
      setPwdLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('settings.title')}</h1>
        <p className="text-gray-500">{t('settings.subtitle')}</p>
      </div>

      <div className="grid gap-6">
        {/* Profile */}
        <div className="card">
          <div className="flex items-center gap-4 mb-4">
            <User className="h-6 w-6 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">{t('settings.profile')}</h2>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">{t('settings.username')}</label>
              <p className="text-gray-900">{user?.username}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">{t('settings.email')}</label>
              {editingEmail ? (
                <div className="flex items-center gap-2 mt-1">
                  <input
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    className="input text-sm py-1"
                    placeholder={t('settings.email_placeholder')}
                    autoFocus
                  />
                  <button
                    onClick={handleEmailSave}
                    disabled={emailLoading}
                    className="btn btn-primary text-xs py-1 px-3"
                  >
                    {emailLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : t('settings.email_save')}
                  </button>
                  <button
                    onClick={() => { setEditingEmail(false); setNewEmail('') }}
                    className="btn btn-secondary text-xs py-1 px-3"
                  >
                    {t('common.cancel')}
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <p className="text-gray-900">{user?.email}</p>
                  <button
                    onClick={() => { setEditingEmail(true); setNewEmail(user?.email || '') }}
                    className="p-1 rounded hover:bg-gray-100"
                    title={t('settings.change_email')}
                  >
                    <Edit2 className="h-3.5 w-3.5 text-gray-400 hover:text-primary-500" />
                  </button>
                </div>
              )}
              {emailMsg && (
                <p className={`text-xs mt-1 ${emailMsg.includes('success') || emailMsg.includes('успешно') ? 'text-success-600' : 'text-danger-600'}`}>
                  {emailMsg}
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">{t('settings.role')}</label>
              <p className="text-gray-900 capitalize">{user?.role}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">{t('settings.status')}</label>
              <span className={`badge ${user?.is_active ? 'badge-success' : 'badge-danger'}`}>
                {user?.is_active ? t('settings.active') : t('settings.inactive')}
              </span>
            </div>
          </div>
        </div>

        {/* Security */}
        <div className="card">
          <div className="flex items-center gap-4 mb-4">
            <Shield className="h-6 w-6 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">{t('settings.security')}</h2>
          </div>
          <div className="space-y-4">
            {!showPwdForm ? (
              <>
                <button
                  onClick={() => setShowPwdForm(true)}
                  className="btn btn-secondary"
                >
                  {t('settings.change_password')}
                </button>
                {pwdMsg && (
                  <div className="flex items-center gap-2 text-sm text-success-600">
                    <CheckCircle className="h-4 w-4" />
                    {pwdMsg}
                  </div>
                )}
              </>
            ) : (
              <form onSubmit={handlePasswordChange} className="space-y-3 max-w-md">
                {pwdError && (
                  <div className="bg-danger-50 border border-danger-500 text-danger-600 px-3 py-2 rounded-lg text-sm">
                    {pwdError}
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('settings.current_password')}</label>
                  <input
                    type="password"
                    required
                    value={currentPwd}
                    onChange={(e) => setCurrentPwd(e.target.value)}
                    className="input mt-1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('settings.new_password')}</label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={newPwd}
                    onChange={(e) => setNewPwd(e.target.value)}
                    className="input mt-1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">{t('settings.confirm_password')}</label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={confirmPwd}
                    onChange={(e) => setConfirmPwd(e.target.value)}
                    className="input mt-1"
                  />
                </div>
                <div className="flex gap-2 pt-2">
                  <button type="submit" disabled={pwdLoading} className="btn btn-primary">
                    {pwdLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        {t('settings.saving')}
                      </>
                    ) : (
                      t('settings.change_password')
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setShowPwdForm(false); setPwdError(''); setCurrentPwd(''); setNewPwd(''); setConfirmPwd('') }}
                    className="btn btn-secondary"
                  >
                    {t('common.cancel')}
                  </button>
                </div>
              </form>
            )}
            <p className="text-sm text-gray-500">
              {t('settings.last_pwd_change')}: {user?.password_changed_at
                ? new Date(user.password_changed_at).toLocaleString()
                : t('settings.never')}
            </p>
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <div className="flex items-center gap-4 mb-4">
            <Bell className="h-6 w-6 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">{t('settings.notifications')}</h2>
          </div>
          <div className="space-y-3">
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="rounded border-gray-300" />
              <span className="text-gray-700">{t('settings.notif_completion')}</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="rounded border-gray-300" />
              <span className="text-gray-700">{t('settings.notif_failures')}</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" className="rounded border-gray-300" />
              <span className="text-gray-700">{t('settings.notif_digest')}</span>
            </label>
            <div className="pt-3 border-t border-gray-100">
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('settings.notif_email')}</label>
              <div className="flex items-center gap-2">
                <input
                  type="email"
                  value={notifEmail}
                  onChange={(e) => setNotifEmail(e.target.value)}
                  onFocus={() => {
                    if (!notifLoaded) {
                      api.get('/notifications/settings').then((r) => {
                        setNotifEmail(r.data.notification_email || '')
                        setNotifLoaded(true)
                      }).catch(() => {})
                    }
                  }}
                  className="input text-sm py-1 flex-1"
                  placeholder={t('settings.notif_email_placeholder')}
                />
                <button
                  onClick={async () => {
                    setNotifLoading(true)
                    setNotifMsg('')
                    try {
                      await api.put('/notifications/email', { email: notifEmail })
                      setNotifMsg(t('settings.notif_saved'))
                      setTimeout(() => setNotifMsg(''), 3000)
                    } catch { setNotifMsg('Error') }
                    finally { setNotifLoading(false) }
                  }}
                  disabled={notifLoading || !notifEmail}
                  className="btn btn-primary text-xs py-1 px-3"
                >
                  {t('settings.notif_save')}
                </button>
                <button
                  onClick={async () => {
                    setNotifLoading(true)
                    setNotifMsg('')
                    try {
                      const r = await api.post('/notifications/test')
                      setNotifMsg(r.data.message || t('settings.notif_sent'))
                      setTimeout(() => setNotifMsg(''), 5000)
                    } catch (err: unknown) {
                      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
                      setNotifMsg(msg || t('settings.notif_not_configured'))
                    }
                    finally { setNotifLoading(false) }
                  }}
                  disabled={notifLoading}
                  className="btn btn-secondary text-xs py-1 px-3"
                >
                  {t('settings.notif_test')}
                </button>
              </div>
              {notifMsg && (
                <p className="text-xs mt-1 text-gray-600">{notifMsg}</p>
              )}
            </div>
          </div>
        </div>

        {/* System Info */}
        <div className="card">
          <div className="flex items-center gap-4 mb-4">
            <Database className="h-6 w-6 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">{t('settings.system')}</h2>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <label className="block text-gray-500">{t('settings.version')}</label>
              <p className="text-gray-900">1.0.0</p>
            </div>
            <div>
              <label className="block text-gray-500">{t('settings.api_endpoint')}</label>
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
