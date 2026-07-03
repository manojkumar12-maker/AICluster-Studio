"use client";

import { ScrollText } from "lucide-react";

export default function LogsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Logs</h1>
        <p className="text-sm text-muted-foreground">System and worker logs</p>
      </div>
      <div className="flex flex-col items-center justify-center rounded-xl border border-border py-16">
        <ScrollText className="mb-4 h-12 w-12 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">Log viewer coming soon</p>
      </div>
    </div>
  );
}
