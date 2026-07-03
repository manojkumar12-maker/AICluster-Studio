import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Search, Check } from 'lucide-react';
import { api } from '../lib/api';

export function DiscoveryPage() {
  const [network, setNetwork] = useState('192.168.1.0/24');
  const { data: discovered, refetch } = useQuery({ queryKey: ['discovery'], queryFn: api.discovery });
  const scanMut = useMutation({ mutationFn: () => api.scan(network), onSuccess: () => refetch() });
  const regMut = useMutation({ mutationFn: (w: any) => api.registerWorker(w), onSuccess: () => refetch() });
  const regAllMut = useMutation({ mutationFn: () => api.registerAll(), onSuccess: () => refetch() });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div><h1 style={{ fontSize: 22, fontWeight: 700 }}>Discovery</h1><p style={{ fontSize: 13, color: '#8888a0' }}>Scan LAN for workers</p></div>
      </div>
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{ flex: 1 }}><label>Network Range</label><input value={network} onChange={(e) => setNetwork(e.target.value)} /></div>
          <button className="btn btn-primary" style={{ alignSelf: 'flex-end' }} onClick={() => scanMut.mutate()} disabled={scanMut.isPending}>
            <Search size={16} /> {scanMut.isPending ? 'Scanning...' : 'Scan LAN'}
          </button>
        </div>
      </div>
      {discovered?.workers?.length > 0 ? (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
            <p style={{ fontSize: 14 }}>{discovered.workers.length} workers found</p>
            <button className="btn btn-primary" onClick={() => regAllMut.mutate()}><Search size={16} /> Register All</button>
          </div>
          {discovered.workers.map((w: any, i: number) => (
            <div key={i} className="card" style={{ marginBottom: 8, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
              <Check size={16} style={{ color: '#22c55e' }} />
              <div style={{ flex: 1 }}><p style={{ fontWeight: 600 }}>{w.hostname}</p><p style={{ fontSize: 12, color: '#8888a0' }}>{w.ip}:{w.port} v{w.version}</p></div>
              <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: w.already_registered ? 'rgba(99,102,241,0.1)' : 'rgba(34,197,94,0.1)', color: w.already_registered ? '#6366f1' : '#22c55e' }}>{w.already_registered ? 'Registered' : 'New'}</span>
              {!w.already_registered && <button className="btn btn-primary" style={{ padding: '4px 12px', fontSize: 12 }} onClick={() => regMut.mutate(w)}>Register</button>}
            </div>
          ))}
        </>
      ) : (
        <div className="card"><p style={{ color: '#8888a0', textAlign: 'center', padding: 20 }}>No workers found. Scan LAN to search.</p></div>
      )}
    </div>
  );
}
