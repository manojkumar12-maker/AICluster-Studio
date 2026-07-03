import { useQuery } from '@tanstack/react-query';
import { Globe } from 'lucide-react';
import { api } from '../lib/api';

export function ClusterPage() {
  const { data: mapData } = useQuery({ queryKey: ['cluster-map'], queryFn: api.clusterMap, refetchInterval: 5000 });
  const { data: health } = useQuery({ queryKey: ['cluster-health'], queryFn: api.clusterHealth, refetchInterval: 5000 });
  const workers = mapData?.workers || [];

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Cluster Map</h1>
      <p style={{ fontSize: 13, color: '#8888a0', marginBottom: 20 }}>Cluster topology and connectivity</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <div className="card"><p style={{ fontSize: 12, color: '#8888a0' }}>Avg CPU</p><p style={{ fontSize: 20, fontWeight: 700 }}>{health?.average_cpu ?? 0}%</p></div>
        <div className="card"><p style={{ fontSize: 12, color: '#8888a0' }}>Avg RAM</p><p style={{ fontSize: 20, fontWeight: 700 }}>{health?.average_ram ?? 0}%</p></div>
        <div className="card"><p style={{ fontSize: 12, color: '#8888a0' }}>Avg Disk</p><p style={{ fontSize: 20, fontWeight: 700 }}>{health?.average_disk ?? 0}%</p></div>
        <div className="card"><p style={{ fontSize: 12, color: '#8888a0' }}>Failed Workers</p><p style={{ fontSize: 20, fontWeight: 700, color: (health?.failed_workers ?? 0) > 0 ? '#ef4444' : '#22c55e' }}>{health?.failed_workers ?? 0}</p></div>
      </div>
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}><Globe size={16} /> Cluster Topology</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ padding: '10px 14px', background: 'rgba(99,102,241,0.1)', borderRadius: 8, border: '1px solid rgba(99,102,241,0.3)' }}>
            <p style={{ fontWeight: 600, color: '#6366f1' }}>Master • {mapData?.master?.hostname || 'localhost'}</p>
            <p style={{ fontSize: 12, color: '#8888a0' }}>{mapData?.master?.ip}:{mapData?.master?.port}</p>
          </div>
          {workers.length === 0 && <p style={{ color: '#8888a0', fontSize: 13, padding: 8 }}>No workers registered</p>}
          {workers.map((w: any) => (
            <div key={w.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 14px', background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
              <span className={`status-dot ${w.status}`} />
              <div style={{ flex: 1 }}><p style={{ fontSize: 14 }}>{w.name}</p><p style={{ fontSize: 12, color: '#8888a0' }}>{w.ip}</p></div>
              <span style={{ fontSize: 12, color: '#8888a0' }}>CPU: {w.cpu_percent}%</span>
              <span style={{ fontSize: 12, color: '#8888a0' }}>RAM: {w.ram_percent}%</span>
              <span className={`badge-${w.status}`} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: w.status === 'online' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)', color: w.status === 'online' ? '#22c55e' : '#ef4444' }}>{w.status}</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div className="card"><h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Worker Versions</h4>{Object.entries(health?.worker_versions || {}).map(([v, c]: any) => <div key={v} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13 }}><span>v{v}</span><span>{c} workers</span></div>)}</div>
        <div className="card"><h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>System Status</h4><div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}><span>Database: {health?.database_status}</span><span>WebSocket: {health?.websocket_status}</span><span>Scheduler: {health?.scheduler_status}</span><span>Network: {health?.network_quality}</span></div></div>
      </div>
    </div>
  );
}
