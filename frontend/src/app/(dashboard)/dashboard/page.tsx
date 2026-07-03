"use client";

import { useQuery } from "@tanstack/react-query";
import { Cpu, HardDrive, Activity } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DashboardData {
  total_workers: number;
  online: number;
  offline: number;
  idle: number;
  busy: number;
  average_cpu: number;
  average_ram: number;
  running_jobs: number;
}

async function fetchDashboard(token: string | null): Promise<DashboardData> {
  if (!token) throw new Error("Not authenticated");
  const res = await fetch(`${API_URL}/api/v1/dashboard`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) {
    useAuthStore.getState().logout();
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  if (!res.ok) throw new Error("Failed to fetch dashboard");
  return res.json();
}

export default function DashboardPage() {
  const token = useAuthStore((s) => s.token);

  const { data: dash, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => fetchDashboard(token),
    refetchInterval: 2000,
    enabled: !!token,
  });

  const cards = [
    {
      title: "Total Workers",
      value: dash?.total_workers ?? "-",
      subtitle: `${dash?.online ?? 0} online`,
      icon: Cpu,
      color: "text-blue-500",
    },
    {
      title: "Running Jobs",
      value: dash?.running_jobs ?? "-",
      subtitle: `${dash?.idle ?? 0} idle workers`,
      icon: Activity,
      color: "text-yellow-500",
    },
    {
      title: "Avg CPU",
      value: dash ? `${dash.average_cpu.toFixed(1)}%` : "-",
      subtitle: "Across all workers",
      icon: Cpu,
      color: "text-green-500",
    },
    {
      title: "Avg RAM",
      value: dash ? `${dash.average_ram.toFixed(1)}%` : "-",
      subtitle: "Across all workers",
      icon: HardDrive,
      color: "text-purple-500",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Cluster overview and real-time metrics
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load metrics. Make sure the backend is running.
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="glass rounded-xl p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">{card.title}</p>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
              <p className="mt-2 text-2xl font-bold">
                {isLoading ? "..." : card.value}
              </p>
              <p className="text-xs text-muted-foreground">{card.subtitle}</p>
            </div>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="glass rounded-xl p-4">
          <h2 className="mb-4 text-sm font-medium">Worker Status</h2>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-5 animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <span className="status-dot online" /> Online
                </span>
                <span className="font-medium">{dash?.online ?? 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <span className="status-dot busy" /> Busy
                </span>
                <span className="font-medium">{dash?.busy ?? 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <span className="status-dot offline" /> Offline
                </span>
                <span className="font-medium">{dash?.offline ?? 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <span className="status-dot paused" /> Idle
                </span>
                <span className="font-medium">{dash?.idle ?? 0}</span>
              </div>
            </div>
          )}
        </div>

        <div className="glass rounded-xl p-4">
          <h2 className="mb-4 text-sm font-medium">Cluster Summary</h2>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-5 animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span>Average CPU</span>
                <span className="font-medium">
                  {dash ? `${dash.average_cpu.toFixed(1)}%` : "-"}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Average RAM</span>
                <span className="font-medium">
                  {dash ? `${dash.average_ram.toFixed(1)}%` : "-"}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Running Jobs</span>
                <span className="font-medium">{dash?.running_jobs ?? 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Online Workers</span>
                <span className="font-medium">{dash?.online ?? 0}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
