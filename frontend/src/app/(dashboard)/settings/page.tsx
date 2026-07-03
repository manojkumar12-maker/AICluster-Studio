"use client";

import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">Cluster configuration</p>
      </div>
      <div className="flex flex-col items-center justify-center rounded-xl border border-border py-16">
        <Settings className="mb-4 h-12 w-12 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">Settings panel coming soon</p>
      </div>
    </div>
  );
}
