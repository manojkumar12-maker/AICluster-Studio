"use client";
import { BarChart3, TrendingUp, Activity } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">Cluster performance and usage analytics.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border p-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2"><BarChart3 className="h-4 w-4" /> CPU Utilization</div>
          <p className="text-2xl font-bold">--</p>
          <p className="text-xs text-muted-foreground mt-1">Requires Prometheus integration</p>
        </div>
        <div className="rounded-lg border p-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2"><Activity className="h-4 w-4" /> Job Throughput</div>
          <p className="text-2xl font-bold">--</p>
          <p className="text-xs text-muted-foreground mt-1">Coming in v1.4.0 with time-series storage</p>
        </div>
        <div className="rounded-lg border p-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2"><TrendingUp className="h-4 w-4" /> Worker Efficiency</div>
          <p className="text-2xl font-bold">--</p>
          <p className="text-xs text-muted-foreground mt-1">Coming in v1.4.0 with historical metrics</p>
        </div>
      </div>
    </div>
  );
}
