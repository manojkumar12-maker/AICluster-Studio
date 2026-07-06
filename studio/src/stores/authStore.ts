import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  username: string | null
  role: string | null
  isAuthenticated: boolean
  login: (token: string, username: string) => void
  logout: () => void
  setRole: (role: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      username: null,
      role: null,
      isAuthenticated: false,
      login: (token: string, username: string) =>
        set({ token, username, isAuthenticated: true }),
      logout: () =>
        set({ token: null, username: null, role: null, isAuthenticated: false }),
      setRole: (role: string) => set({ role }),
    }),
    { name: 'aicluster-auth' },
  ),
)
