"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Cpu,
  Briefcase,
  Bot,
  FolderTree,
  Files,
  ScrollText,
  BarChart3,
  Settings,
  Info,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/workers", label: "Workers", icon: Cpu },
  { href: "/jobs", label: "Jobs", icon: Briefcase },
  { href: "/chat", label: "AI Chat", icon: Bot },
  { href: "/projects", label: "Projects", icon: FolderTree },
  { href: "/files", label: "Files", icon: Files },
  { href: "/logs", label: "Logs", icon: ScrollText },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/about", label: "About", icon: Info },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar-gradient flex w-56 flex-col border-r border-border">
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
          <Cpu className="h-4 w-4 text-primary-foreground" />
        </div>
        <span className="text-sm font-semibold text-gradient">AICluster</span>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-sidebar-accent/10 text-sidebar-accent"
                  : "text-sidebar-foreground/60 hover:bg-sidebar-border/20 hover:text-sidebar-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-3">
        <p className="text-[10px] text-muted-foreground">
          AICluster v1.0.0
        </p>
      </div>
    </aside>
  );
}
