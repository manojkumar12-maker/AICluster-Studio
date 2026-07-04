"use client";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import { FolderGit2, Loader2 } from "lucide-react";

export default function ProjectsPage() {
  const token = useAuthStore((s) => s.token);
  const { data, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: async () => {
      const res = await fetch("/api/v1/studio/projects", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch");
      return res.json();
    },
  });
  const projects = Array.isArray(data) ? data : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
        <p className="text-muted-foreground">Development projects tracked in AICluster Studio.</p>
      </div>
      {isLoading ? <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin" /></div>
      : projects.length === 0 ? (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <FolderGit2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="font-medium">No projects</h3>
          <p className="text-sm text-muted-foreground mt-1">Create projects in AICluster Studio to manage development workflows.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {projects.map((p: any) => (
            <div key={p.id} className="rounded-lg border p-4">
              <h3 className="font-medium">{p.name}</h3>
              <p className="text-sm text-muted-foreground">{p.description || "No description"}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
