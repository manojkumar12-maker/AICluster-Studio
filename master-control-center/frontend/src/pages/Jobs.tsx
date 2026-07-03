import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export function JobsPage() {
  const { data } = useQuery({ queryKey: ['cluster-health'], queryFn: api.clusterHealth, refetchInterval: 3000 });
  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Jobs</h1>
      <p style={{ fontSize: 13, color: '#8888a0', marginBottom: 20 }}>Cluster job summary</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
        <div className="card"><p style={{ fontSize: 12, color: '#8888a0' }}>Total Jobs</p><p style={{ fontSize: 28, fontWeight: 700, marginTop: 4 }}>{data?.total_jobs ?? 0}</p></div>
        <div className="card"><p style={{ fontSize: 12, color: '#8888a0' }}>Queued</p><p style={{ fontSize: 28, fontWeight: 700, marginTop: 4, color: '#eab308' }}>{data?.queued_jobs ?? 0}</p></div>
        <div className="card"><p style={{ fontSize: 12, color: '#8888a0' }}>Running</p><p style={{ fontSize: 28, fontWeight: 700, marginTop: 4, color: '#6366f1' }}>{data?.running_jobs ?? 0}</p></div>
        <div className="card"><p style={{ fontSize: 12, color: '#8888a0' }}>Completed</p><p style={{ fontSize: 28, fontWeight: 700, marginTop: 4, color: '#22c55e' }}>{data?.completed_jobs ?? 0}</p></div>
        <div className="card"><p style={{ fontSize: 12, color: '#8888a0' }}>Failed</p><p style={{ fontSize: 28, fontWeight: 700, marginTop: 4, color: '#ef4444' }}>{data?.failed_jobs ?? 0}</p></div>
        <div className="card"><p style={{ fontSize: 12, color: '#8888a0' }}>Scheduler</p><p style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{data?.scheduler_status || 'unknown'}</p></div>
      </div>
    </div>
  );
}
