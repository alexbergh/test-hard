import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../lib/api'

interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  is_superuser: boolean
  must_change_password: boolean
  password_changed_at: string | null
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  mustChangePassword: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      mustChangePassword: false,

      login: async (username: string, password: string) => {
        const response = await api.post('/auth/login', { username, password })
        const { access_token, must_change_password } = response.data
        set({ token: access_token, isAuthenticated: true, mustChangePassword: must_change_password })
        await get().fetchUser()
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false, mustChangePassword: false })
      },

      fetchUser: async () => {
        try {
          const response = await api.get('/auth/me')
          set({ user: response.data, mustChangePassword: response.data.must_change_password })
        } catch {
          get().logout()
        }
      },

      changePassword: async (currentPassword: string, newPassword: string) => {
        await api.post('/auth/change-password', {
          current_password: currentPassword,
          new_password: newPassword,
        })
        set({ mustChangePassword: false })
        const user = get().user
        if (user) {
          set({ user: { ...user, must_change_password: false } })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, user: state.user, isAuthenticated: state.isAuthenticated, mustChangePassword: state.mustChangePassword }),
    }
  )
)
