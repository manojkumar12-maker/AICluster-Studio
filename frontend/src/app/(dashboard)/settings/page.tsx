"use client";
import { useAuthStore } from "@/stores/auth-store";
import { Settings, Shield, Server } from "lucide-react";

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Cluster configuration and preferences.</p>
      </div>
      <div className="space-y-4">
        <div className="rounded-lg border p-4">
          <div className="flex items-center gap-2 mb-2"><Shield className="h-4 w-4" /><h3 className="font-medium">Account</h3></div>
          <p className="text-sm text-muted-foreground">Signed in as <span className="font-mono">{user?.username || "admin"}</span></p>
          <p className="text-sm text-muted-foreground">Role: {user?.role || "admin"}</p>
        </div>
        <div className="rounded-lg border p-4">
          <div className="flex items-center gap-2 mb-2"><Server className="h-4 w-4" /><h3 className="font-medium">Cluster</h3></div>
          <p className="text-sm text-muted-foreground">Full cluster configuration editing is available in the Master Control Center desktop application.</p>
        </div>
        <div className="rounded-lg border p-4">
          <div className="flex items-center gap-2 mb-2"><Settings className="h-4 w-4" /><h3 className="font-medium">Preferences</h3></div>
          <p className="text-sm text-muted-foreground">Dashboard
