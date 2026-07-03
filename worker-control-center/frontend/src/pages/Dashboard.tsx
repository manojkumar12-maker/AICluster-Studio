import { useQuery } from '@tanstack/react-query';
import { Cpu, HardDrive, Activity, Play, Square, RotateCcw, RefreshCw } from 'lucide-react';
import { api, type StatusData } from '../lib/api';

function MetricCard({ title, value, subtitle, icon, color }: { title: string; value: string; subtitle?: string; icon: React.ReactNode; color: string }) {
  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>{title}</p>
          <p style={{ fontSize: 24, fontWeight: 700 }}>{value}</p>
          {subtitle && <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{subtitle}</p>}
        </div>
        <div style={{ color }}>{icon}</div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { data: status, isLoading, refetch } = useQuery<StatusData>({
    queryKey: ['status'],
    queryFn: api.getStatus,
    refetchInterval: 3000,
  });

  const hbColor = status?.heartbeat_status === 'ok' ? 'var(--success)' : status?.heartbeat_status === 'unreachable' ? 'var(--error)' : 'var(--warning)';

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Worker Dashboard</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Live status and metrics</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {status?.status !== 'running' ? (
            <button className="btn btn-success" onClick={() => { api.startWorker(); setTimeout(refetch, 1000); }}>
              <Play size={16} /> Start
            </button>
          ) : (
            <button className="btn btn-error" onClick={() => { api.stopWorker(); setTimeout(refetch, 1000); }}>
              <Square size={16} /> Stop
            </button>
          )}
          <button className="btn btn-secondary" onClick={() => { api.restartWorker(); setTimeout(refetch, 2000); }}>
            <RotateCcw size={16} /> Restart
          </button>
          <button className="btn btn-secondary" onClick={() => refetch()}>
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <div className="card" style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 12, padding: '12px 20px' }}>
          <span className={`status-dot ${status?.status === 'running' ? 'online' : 'offline'}`} />
          <div>
            <p style={{ fontSize: 13, fontWeight: 600 }}>Worker {status?.status === 'running' ? 'Running' : 'Stopped'}</p>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{status?.worker_name || '-'}</p>
          </div>
        </div>
        <div className="card" style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 12, padding: '12px 20px' }}>
          <span className="status-dot" style={{ background: hbColor }} />
          <div>
            <p style={{ fontSize: 13, fontWeight: 600 }}>Heartbeat: {status?.heartbeat_status || 'unknown'}</p>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>ID: {(status?.worker_id || '-').slice(0, 12)}...</p>
          </div>
        </div>
        <div className="card" style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 12, padding: '12px 20px' }}>
          <Cpu size={20} style={{ color: 'var(--accent)' }} />
          <div>
            <p style={{ fontSize: 13, fontWeight: 600 }}>Connection Quality</p>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{status?.connection_quality || 'unknown'}</p>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <MetricCard title="CPU" value={isLoading ? '...' : `${status?.cpu_percent ?? 0}%`} icon={<Cpu size={20} />} color="var(--accent)" />
        <MetricCard title="RAM" value={isLoading ? '...' : `${status?.ram_percent ?? 0}%`} icon={<HardDrive size={20} />} color="var(--success)" />
        <MetricCard title="Disk" value={isLoading ? '...' : `${status?.disk_percent ?? 0}%`} icon={<HardDrive size={20} />} color="var(--warning)" />
        <MetricCard title="Uptime" value={isLoading ? '...' : `${Math.round((status?.uptime_seconds ?? 0) / 60)}m`} icon={<Activity size={20} />} color="var(--accent)" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginBottom: 20 }}>
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Job Summary</h3>
          <div style={{ display: 'flex', gap: 24 }}>
            <div>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Completed</p>
              <p style={{ fontSize: 20, fontWeight: 700, color: 'var(--success)' }}>{status?.jobs_completed ?? 0}</p>
            </div>
            <div>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Failed</p>
              <p style={{ fontSize: 20, fontWeight: 700, color: 'var(--error)' }}>{status?.jobs_failed ?? 0}</p>
            </div>
            <div>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Current Job</p>
              <p style={{ fontSize: 14, fontWeight: 600 }}>{status?.current_job ? (status.current_job).slice(0, 12) + '...' : 'None'}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Network</h3>
          <div style={{ display: 'flex', gap: 24 }}>
            <div>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Master</p>
              <p style={{ fontSize: 14, fontWeight: 600 }}>{status?.master_url || '-'}</p>
            </div>
            <div>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Last Heartbeat</p>
              <p style={{ fontSize: 13 }}>{status?.last_heartbeat ? new Date(status.last_heartbeat).toLocaleTimeString() : '-'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
