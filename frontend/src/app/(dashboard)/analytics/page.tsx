"use client";

import { BarChart3 } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-sm text-muted-foreground">Cluster performance and metrics</p>
      </div>
      <div className="flex flex-col items-center justify-center rounded-xl border border-border py-16">
        <BarChart3 className="mb-4 h-12 w-12 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">Analytics dashboard coming soon</p>
      </div>
    </div>
  );
}
