import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { api } from '../lib/api';

export function LogsPage() {
  const [filter, setFilter] = useState('');
  const { data, isLoading } = useQuery({ queryKey: ['logs'], queryFn: () => api.getLogs(""), refetchInterval: 5000 });
  const entries = data?.entries || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Logs</h1>
      <p style={{ fontSize: 13, color: '#8888a0', marginBottom: 16 }}>Master logs</p>
      <div style={{ position: 'relative', marginBottom: 16 }}>
        <Search size={16} style={{ position: 'absolute', left: 10, top: 12, color: '#8888a0' }} />
        <input style={{ paddingLeft: 32 }} placeholder="Search logs..." value={filter} onChange={(e) => setFilter(e.target.value)} />
      </div>
      <div className="card" style={{ flex: 1, overflow: 'auto', fontFamily: 'monospace', fontSize: 12 }}>
        {isLoading && <p style={{ color: '#8888a0', padding: 16 }}>Loading...</p>}
        {!isLoading && entries.length === 0 && <p style={{ color: '#8888a0', padding: 16 }}>No entries</p>}
        {entries.filter((e: any) => !filter || e.message.includes(filter)).map((e: any, i: number) => (
          <div key={i} style={{ padding: '3px 8', borderRadius: 4, background: i % 2 === 0 ? 'rgba(0,0,0,0.1)' : 'transparent' }}>
            <span style={{ color: '#8888a0' }}>{e.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
