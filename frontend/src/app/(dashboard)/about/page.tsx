"use client";

import { Cpu } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">About</h1>
        <p className="text-sm text-muted-foreground">AICluster platform information</p>
      </div>
      <div className="glass rounded-xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
            <Cpu className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">AICluster</h2>
            <p className="text-xs text-muted-foreground">Version 1.0.0</p>
          </div>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">
          AICluster is an offline AI cluster management platform that enables you
          to distribute AI workloads across multiple Windows computers on your
          local network. It intelligently manages worker resources to ensure
          office workers never experience performance degradation.
        </p>
      </div>
    </div>
  );
}
