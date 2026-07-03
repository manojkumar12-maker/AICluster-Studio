import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserResponse } from "@/types";

interface AuthState {
  token: string | null;
  user: UserResponse | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,

      login: async (username: string, password: string) => {
        const res = await fetch(`${API_URL}/api/v1/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        if (!res.ok) {
          if (res.status === 401) {
            throw new Error("Invalid credentials");
          }
          if (res.status >= 500) {
            throw new Error("Server error. Please try again later.");
          }
          throw new Error(`Login failed (${res.status})`);
        }

        const data = await res.json();
        set({ token: data.access_token, user: data.user });
      },

      logout: () => {
        set({ token: null, user: null });
      },
    }),
    {
      name: "aicluster-auth",
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
);
