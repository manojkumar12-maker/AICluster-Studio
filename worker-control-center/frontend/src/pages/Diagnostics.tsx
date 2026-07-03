import { useQuery } from '@tanstack/react-query';
import { Check, X, AlertTriangle, Cpu, Globe } from 'lucide-react';
import { api, type SystemInfo } from '../lib/api';

function DiagItem({ label, ok, suggestion }: { label: string; ok: boolean; suggestion?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', background: 'rgba(0,0,0,0.15)', borderRadius: 8 }}>
      {ok ? <Check size={16} style={{ color: 'var(--success)' }} /> : <X size={16} style={{ color: 'var(--error)' }} />}
      <span style={{ flex: 1, fontSize: 14 }}>{label}</span>
      {!ok && suggestion && <span style={{ fontSize: 12, color: 'var(--warning)', maxWidth: 200, textAlign: 'right' }}>{suggestion}</span>}
    </div>
  );
}

export function DiagnosticsPage() {
  const { data: sys, isLoading } = useQuery<SystemInfo>({ queryKey: ['sysinfo'], queryFn: api.getSystemInfo });
  const { data: status } = useQuery({ queryKey: ['status'], queryFn: api.getStatus, refetchInterval: 5000 });

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Diagnostics</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>System health checks</p>

      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Running diagnostics...</p>}

      {sys && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Cpu size={16} /> System
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <DiagItem label={`OS: ${sys.os} ${sys.os_version}`} ok />
              <DiagItem label={`Python: ${sys.python_version.split(' ')[0]}`} ok />
              <DiagItem label={`Git Installed`} ok={sys.git_installed} suggestion="Install Git from git-scm.com" />
              <DiagItem label={`Disk Space: ${sys.disk_free_gb}GB free`} ok={sys.disk_free_gb > 1} suggestion="Free up at least 1GB" />
              <DiagItem label={`RAM: ${sys.ram_total_gb}GB total`} ok={sys.ram_total_gb > 2} suggestion="Minimum 2GB RAM required" />
              <DiagItem label={`CPU Cores: ${sys.cpu_count}`} ok={(sys.cpu_count ?? 0) > 1} suggestion="Minimum 2 cores required" />
              <DiagItem label={`Administrator Rights`} ok={sys.is_admin} suggestion="Run as Administrator" />
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Globe size={16} /> Network
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <DiagItem label={`Master Online`} ok={sys.master_online} suggestion="Ensure Master is running" />
              <DiagItem label={`Worker Folder`} ok={sys.worker_folder_exists} suggestion="Install worker first" />
              <DiagItem label={`Log Folder`} ok={sys.log_folder_exists} />
              <DiagItem label={`File Permissions`} ok={sys.has_permissions} suggestion="Check folder permissions" />
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Activity size={16} /> Worker Status
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <DiagItem label={`Worker Running`} ok={status?.status === 'running'} suggestion="Start worker on Dashboard" />
              <DiagItem label={`Heartbeat Active`} ok={status?.heartbeat_status === 'ok'} suggestion="Check master connection" />
              <DiagItem label={`Registered with Master`} ok={!!status?.worker_id} suggestion="Register worker" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Activity(props: any) { return <AlertTriangle size={16} {...props} />; }
