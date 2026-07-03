"use client";

import { Briefcase } from "lucide-react";

export default function JobsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Jobs</h1>
        <p className="text-sm text-muted-foreground">Manage job queue and history</p>
      </div>
      <div className="flex flex-col items-center justify-center rounded-xl border border-border py-16">
        <Briefcase className="mb-4 h-12 w-12 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">Job management coming soon</p>
      </div>
    </div>
  );
}
