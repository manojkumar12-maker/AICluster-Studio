"use client";

import { FolderTree } from "lucide-react";

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Projects</h1>
        <p className="text-sm text-muted-foreground">Browse and manage projects</p>
      </div>
      <div className="flex flex-col items-center justify-center rounded-xl border border-border py-16">
        <FolderTree className="mb-4 h-12 w-12 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">Project explorer coming soon</p>
      </div>
    </div>
  );
}
