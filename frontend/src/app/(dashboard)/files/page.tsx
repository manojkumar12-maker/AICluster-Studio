"use client";

import { Files } from "lucide-react";

export default function FilesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Files</h1>
        <p className="text-sm text-muted-foreground">Manage shared files and datasets</p>
      </div>
      <div className="flex flex-col items-center justify-center rounded-xl border border-border py-16">
        <Files className="mb-4 h-12 w-12 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">File manager coming soon</p>
      </div>
    </div>
  );
}
