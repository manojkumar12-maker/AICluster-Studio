import { useQuery, useMutation } from '@tanstack/react-query';
import { Cpu, HardDrive, Wifi, Thermometer, RotateCcw, Wrench } from 'lucide-react';
import { api } from '../lib/api';

export function WorkersPage() {
  const { data, refetch } = useQuery({ queryKey: ['workers'], queryFn: api.clusterWorkers, refetchInterval: 3000 });
  const maintMut = useMutation({ mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) => api.setMaintenance(id, enabled), onSuccess: () => refetch() });
  const workers = data?.workers || [];

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Workers</h1>
      <p style={{ fontSize: 13, color: '#8888a0', marginBottom: 20 }}>{workers.length} workers in cluster</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 12 }}>
        {workers.map((w: any) => (
          <div key={w.id} className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span className={`status-dot ${w.status === 'online' ? 'online' : w.status === 'busy' ? 'busy' : w.status === 'paused' ? 'paused' : 'offline'}`} />
              <div style={{ flex: 1 }}><p style={{ fontWeight: 600 }}>{w.worker_name}</p><p style={{ fontSize: 12, color: '#8888a0' }}>{w.hostname} • {w.ip}</p></div>
              <span className={`badge-${w.status}`} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: w.status === 'online' ? 'rgba(34,197,94,0.1)' : w.status === 'busy' ? 'rgba(234,179,8,0.1)' : 'rgba(239,68,68,0.1)', color: w.status === 'online' ? '#22c55e' : w.status === 'busy' ? '#eab308' : '#ef4444' }}>{w.status}</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 13 }}>
              <div><Cpu size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />CPU: {w.cpu_percent}%</div>
              <div><HardDrive size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />RAM: {w.ram_percent}%</div>
              <div><Wifi size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />v{w.version}</div>
              <div><Thermometer size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />Job: {(w.current_job || '-').slice(0, 12)}</div>
            </div>
            <div style={{ display: 'flex', gap: 6, marginTop: 12 }}>
              <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}><RotateCcw size={12} /> Restart</button>
              <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => maintMut.mutate({ id: w.id, enabled: !w.is_paused })}>
                <Wrench size={12} /> {w.is_paused ? 'Resume' : 'Maintenance'}
              </button>
              <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}>Logs</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
