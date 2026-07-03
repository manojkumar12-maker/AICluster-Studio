"use client";

import { useQuery } from "@tanstack/react-query";
import { Cpu, HardDrive, Wifi, Thermometer } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import type { WorkerResponse } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchWorkers(token: string | null): Promise<WorkerResponse[]> {
  if (!token) throw new Error("Not authenticated");
  const res = await fetch(`${API_URL}/api/v1/workers`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) {
    useAuthStore.getState().logout();
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  if (!res.ok) throw new Error("Failed to fetch workers");
  return res.json();
}

export default function WorkersPage() {
  const token = useAuthStore((s) => s.token);

  const { data: workers, isLoading, error } = useQuery({
    queryKey: ["workers"],
    queryFn: () => fetchWorkers(token),
    refetchInterval: 3000,
    enabled: !!token,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Workers</h1>
        <p className="text-sm text-muted-foreground">
          Manage and monitor worker nodes
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load workers. Make sure the backend is running.
        </div>
      )}

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="glass rounded-xl p-4">
              <div className="mb-3 h-5 w-32 animate-pulse rounded bg-muted" />
              <div className="space-y-2">
                {[...Array(4)].map((_, j) => (
                  <div key={j} className="h-4 animate-pulse rounded bg-muted" />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : workers && workers.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workers.map((worker) => (
            <div key={worker.id} className="glass rounded-xl p-4">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-medium">{worker.worker_name}</h3>
                <span className={`status-dot ${worker.status}`} />
              </div>
              <div className="space-y-2 text-sm text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Cpu className="h-3.5 w-3.5" /> CPU
                  </span>
                  <span className="font-medium text-foreground">
                    {worker.cpu_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <HardDrive className="h-3.5 w-3.5" /> RAM
                  </span>
                  <span className="font-medium text-foreground">
                    {worker.ram_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <HardDrive className="h-3.5 w-3.5" /> Disk
                  </span>
                  <span className="font-medium text-foreground">
                    {worker.disk_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Wifi className="h-3.5 w-3.5" /> IP
                  </span>
                  <span className="font-medium text-foreground">{worker.ip}</span>
                </div>
                {worker.temperature && (
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Thermometer className="h-3.5 w-3.5" /> Temp
                    </span>
                    <span className="font-medium text-foreground">
                      {worker.temperature.toFixed(1)}°C
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border py-16">
          <Cpu className="mb-4 h-12 w-12 text-muted-foreground/50" />
          <p className="text-sm text-muted-foreground">
            No workers registered. Start a worker agent to see it here.
          </p>
        </div>
      )}
    </div>
  );
}
