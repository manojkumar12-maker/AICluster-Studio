import { useQuery } from '@tanstack/react-query';
import { Check, X, AlertTriangle } from 'lucide-react';
import { api } from '../lib/api';

export function DiagnosticsPage() {
  const { data: diag } = useQuery({ queryKey: ['diagnostics'], queryFn: api.diagnostics, refetchInterval: 10000 });
  const results = diag?.results || [];

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Diagnostics</h1>
      <p style={{ fontSize: 13, color: '#8888a0', marginBottom: 20 }}>System health checks</p>
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>All Tests</h3>
        {results.map((r: any, i: number) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: i < results.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
            {r.status === 'pass' ? <Check size={16} style={{ color: '#22c55e' }} /> : r.status === 'warning' ? <AlertTriangle size={16} style={{ color: '#eab308' }} /> : <X size={16} style={{ color: '#ef4444' }} />}
            <span style={{ flex: 1, fontSize: 14 }}>{r.test}</span>
            <span className={`badge-${r.status}`} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: r.status === 'pass' ? 'rgba(34,197,94,0.1)' : r.status === 'warning' ? 'rgba(234,179,8,0.1)' : 'rgba(239,68,68,0.1)', color: r.status === 'pass' ? '#22c55e' : r.status === 'warning' ? '#eab308' : '#ef4444' }}>{r.status.toUpperCase()}</span>
            <span style={{ fontSize: 12, color: '#8888a0' }}>{r.detail}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
