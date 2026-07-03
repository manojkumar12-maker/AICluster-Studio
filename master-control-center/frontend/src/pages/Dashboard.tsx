import { useQuery } from '@tanstack/react-query';
import { Cpu, HardDrive, Activity, Server, Wifi, Database } from 'lucide-react';
import { api } from '../lib/api';

function Metric({ title, value, icon, color }: { title: string; value: string; icon: React.ReactNode; color: string }) {
  return <div className="card" style={{ flex: 1 }}><div style={{ display: 'flex', justifyContent: 'space-between' }}><div><p style={{ fontSize: 12, color: '#8888a0' }}>{title}</p><p style={{ fontSize: 22, fontWeight: 700, marginTop: 4 }}>{value}</p></div><div style={{ color }}>{icon}</div></div></div>;
}

export function DashboardPage() {
  const { data: status } = useQuery({ queryKey: ['cluster-status'], queryFn: api.clusterStatus, refetchInterval: 3000 });
  const { data: health } = useQuery({ queryKey: ['cluster-health'], queryFn: api.clusterHealth, refetchInterval: 5000 });

  return (
    <div>
      <div style={{ marginBottom: 24 }}><h1 style={{ fontSize: 22, fontWeight: 700 }}>Cluster Dashboard</h1><p style={{ fontSize: 13, color: '#8888a0' }}>Master Control Center</p></div>
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <div className="card" style={{ flex: 1, padding: '12px 20px', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className={`status-dot ${status?.master_status === 'online' ? 'online' : 'offline'}`} />
          <div><p style={{ fontWeight: 600 }}>Master {status?.master_status === 'online' ? 'Online' : 'Offline'}</p><p style={{ fontSize: 12, color: '#8888a0' }}>v{status?.version || '-'}</p></div>
        </div>
        <div className="card" style={{ flex: 1, padding: '12px 20px', display: 'flex', alignItems: 'center', gap: 10 }}>
          <Database size={20} style={{ color: '#6366f1' }} />
          <div><p style={{ fontWeight: 600 }}>Database</p><p style={{ fontSize: 12, color: '#8888a0' }}>{status?.database || 'unknown'}</p></div>
        </div>
        <div className="card" style={{ flex: 1, padding: '12px 20px', display: 'flex', alignItems: 'center', gap: 10 }}>
          <Wifi size={20} style={{ color: status?.websocket_status === 'connected' ? '#22c55e' : '#ef4444' }} />
          <div><p style={{ fontWeight: 600 }}>WebSocket</p><p style={{ fontSize: 12, color: '#8888a0' }}>{status?.websocket_status || 'disconnected'}</p></div>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <Metric title="Online Workers" value={String(status?.online_workers ?? 0)} icon={<Cpu size={20} />} color="#22c55e" />
        <Metric title="Offline" value={String(status?.offline_workers ?? 0)} icon={<Cpu size={20} />} color="#ef4444" />
        <Metric title="Busy" value={String(status?.busy_workers ?? 0)} icon={<Activity size={20} />} color="#eab308" />
        <Metric title="Running Jobs" value={String(health?.running_jobs ?? 0)} icon={<Server size={20} />} color="#6366f1" />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <Metric title="Avg CPU" value={health ? `${health.average_cpu}%` : '-'} icon={<Cpu size={20} />} color="#6366f1" />
        <Metric title="Avg RAM" value={health ? `${health.average_ram}%` : '-'} icon={<HardDrive size={20} />} color="#22c55e" />
        <Metric title="Queued Jobs" value={String(health?.queued_jobs ?? 0)} icon={<Activity size={20} />} color="#eab308" />
        <Metric title="Failed Jobs" value={String(health?.failed_jobs ?? 0)} icon={<Activity size={20} />} color="#ef4444" />
      </div>
      <div className="card" style={{ marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Master Status</h3>
        <div style={{ display: 'flex', gap: 24 }}>
          <div><p style={{ fontSize: 11, color: '#8888a0' }}>Uptime</p><p style={{ fontSize: 16, fontWeight: 700 }}>{status?.uptime_seconds ? `${Math.round(status.uptime_seconds / 86400)}d` : '-'}</p></div>
          <div><p style={{ fontSize: 11, color: '#8888a0' }}>CPU</p><p style={{ fontSize: 16, fontWeight: 700 }}>{status?.cpu_percent ?? 0}%</p></div>
          <div><p style={{ fontSize: 11, color: '#8888a0' }}>RAM</p><p style={{ fontSize: 16, fontWeight: 700 }}>{status?.ram_percent ?? 0}%</p></div>
          <div><p style={{ fontSize: 11, color: '#8888a0' }}>Disk</p><p style={{ fontSize: 16, fontWeight: 700 }}>{status?.disk_percent ?? 0}%</p></div>
          <div><p style={{ fontSize: 11, color: '#8888a0' }}>Last Backup</p><p style={{ fontSize: 14 }}>{status?.last_backup || 'Never'}</p></div>
        </div>
      </div>
    </div>
  );
}
