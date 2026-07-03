import { useQuery, useMutation } from '@tanstack/react-query';
import { Bell, Check } from 'lucide-react';
import { api } from '../lib/api';

export function NotificationsPage() {
  const { data, refetch } = useQuery({ queryKey: ['alerts'], queryFn: api.getAlerts, refetchInterval: 5000 });
  const markMut = useMutation({ mutationFn: () => api.markAlertsRead(), onSuccess: () => refetch() });
  const alerts = data?.alerts || [];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
        <div><h1 style={{ fontSize: 22, fontWeight: 700 }}>Alerts</h1><p style={{ fontSize: 13, color: '#8888a0' }}>Cluster notifications</p></div>
        {alerts.length > 0 && <button className="btn btn-secondary" onClick={() => markMut.mutate()}><Check size={16} /> Mark All Read</button>}
      </div>
      <div className="card">
        {alerts.length === 0 && <p style={{ color: '#8888a0', textAlign: 'center', padding: 20 }}>No alerts</p>}
        {alerts.map((a: any, i: number) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: i < alerts.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
            <Bell size={16} style={{ color: a.read ? '#8888a0' : '#6366f1' }} />
            <span style={{ flex: 1, fontSize: 14 }}>{a.message}</span>
            <span style={{ fontSize: 12, color: '#8888a0' }}>{a.timestamp}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
