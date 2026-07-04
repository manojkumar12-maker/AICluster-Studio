"use client";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import { Clock, CheckCircle, XCircle, Loader2 } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  queued: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  running: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  completed: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  failed: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  cancelled: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400",
};

export default function JobsPage() {
  const token = useAuthStore((s) => s.token);
  const { data, isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => {
      const res = await fetch("/api/v1/jobs", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch jobs");
      return res.json();
    },
    refetchInterval: 5000,
  });

  if (isLoading) return <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin" /></div>;

  const jobs = Array.isArray(data) ? data : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Jobs</h1>
        <p className="text-muted-foreground">Monitor job execution across the cluster.</p>
      </div>
      {jobs.length === 0 ? (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <h3 className="font-medium">No jobs</h3>
          <p className="text-sm text-muted-foreground mt-1">Jobs will appear here when created.</p>
        </div>
      ) : (
        <div className="rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-3 font-medium">Type</th>
                <th className="text-left p-3 font-medium">Status</th>
                <th className="text-left p-3 font-medium">Priority</th>
                <th className="text-left p-3 font-medium">Progress</th>
                <th className="text-left p-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {jobs.map((job: any) => (
                <tr key={job.id} className="hover:bg-muted/30">
                  <td className="p-3 capitalize">{job.type}</td>
                  <td className="p-3">
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[job.status] || ""}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="p-3">{job.priority}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <div className="h-2 flex-1 rounded-full bg-muted overflow-hidden">
                        <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${job.progress || 0}%` }} />
                      </div>
                      <span className="text-xs w-8 text-right">{Math.round(job.progress || 0)}%</span>
                    </div>
                  </td>
                  <td className="p-3 text-xs text-muted-foreground">{new Date(job.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
