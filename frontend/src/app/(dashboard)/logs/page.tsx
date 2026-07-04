"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import { Loader2, AlertTriangle, Info, AlertCircle } from "lucide-react";

const LEVEL_ICONS: Record<string, React.ReactNode> = {
  info: <Info className="h-4 w-4 text-blue-500" />,
  warning: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
  error: <AlertCircle className="h-4 w-4 text-red-500" />,
};

export default function LogsPage() {
  const token = useAuthStore((s) => s.token);
  const [level, setLevel] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["logs", level],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (level) params.set("level", level);
      const res = await fetch(`/api/v1/logs?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch logs");
      return res.json();
    },
    refetchInterval: 10000,
  });

  const logs = Array.isArray(data) ? data : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Logs</h1>
          <p className="text-muted-foreground">System-wide event log with filtering.</p>
        </div>
        <select
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
        >
          <option value="">All Levels</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
        </select>
      </div>
      {isLoading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
      ) : logs.length === 0 ? (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <h3 className="font-medium">No logs</h3>
          <p className="text-sm text-muted-foreground mt-1">Log entries will appear as system events occur.</p>
        </div>
      ) : (
        <div className="rounded-lg border overflow-hidden">
          <div className="max-h-[600px] overflow-y-auto font-mono text-xs">
            {logs.map((log: any) => (
              <div key={log.id} className="flex items-start gap-3 border-b px-4 py-2 hover:bg-muted/30">
                <span className="text-muted-foreground shrink-0 w-16">{new Date(log.created_at).toLocaleTimeString()}</span>
                <span className="shrink-0">{LEVEL_ICONS[log.level]}</span>
                <span className="shrink-0 font-semibold uppercase w-16">{log.level}</span>
                <span className="text-muted-foreground shrink-0 w-24">{log.source}</span>
                <span className="flex-1">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
