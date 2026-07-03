"use client";

import { useRouter } from "next/navigation";
import { Search, Bell, LogOut, Settings } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";

export function Topbar() {
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="flex h-14 items-center gap-4 border-b border-border bg-background/80 px-6 backdrop-blur-sm">
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          placeholder="Search workers, jobs, files..."
          className="w-full rounded-lg border border-border bg-background py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      <div className="flex items-center gap-3">
        <button className="relative rounded-lg p-2 text-muted-foreground hover:bg-accent">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-destructive" />
        </button>

        <button className="rounded-lg p-2 text-muted-foreground hover:bg-accent">
          <Settings className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-2 border-l border-border pl-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
            {user?.username?.charAt(0).toUpperCase() || "U"}
          </div>
          <span className="text-xs text-muted-foreground">
            {user?.username || "User"}
          </span>
          <button
            onClick={handleLogout}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
}
