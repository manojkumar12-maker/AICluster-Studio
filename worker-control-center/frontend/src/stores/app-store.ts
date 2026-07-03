import { create } from 'zustand';

interface AppState {
  sidebarOpen: boolean;
  currentPage: string;
  darkMode: boolean;
  toggleSidebar: () => void;
  setPage: (page: string) => void;
  toggleDarkMode: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  currentPage: 'dashboard',
  darkMode: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setPage: (page: string) => set({ currentPage: page }),
  toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
}));
