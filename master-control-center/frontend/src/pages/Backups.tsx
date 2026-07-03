import { useQuery, useMutation } from '@tanstack/react-query';
import { Download } from 'lucide-react';
import { api } from '../lib/api';

export function BackupsPage() {
  const { data: backups, refetch } = useQuery({ queryKey: ['backups'], queryFn: api.listBackups });
  const backupMut = useMutation({ mutationFn: () => api.backup(), onSuccess: () => refetch() });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
        <div><h1 style={{ fontSize: 22, fontWeight: 700 }}>Backups</h1><p style={{ fontSize: 13, color: '#8888a0' }}>Cluster backup and restore</p></div>
        <button className="btn btn-primary" onClick={() => backupMut.mutate()} disabled={backupMut.isPending}>
          <Download size={16} /> {backupMut.isPending ? 'Backing up...' : 'Create Backup'}
        </button>
      </div>
      {backupMut.data && (
        <div className="card" style={{ marginBottom: 16, borderColor: '#22c55e' }}>
          <p style={{ color: '#22c55e' }}>Backup created: {backupMut.data.file}</p>
          <p style={{ fontSize: 12, color: '#8888a0' }}>Size: {(backupMut.data.size_bytes / 1024).toFixed(1)}KB</p>
        </div>
      )}
      <div className="card">
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Backup History</h3>
        {backups?.backups?.length > 0 ? backups.backups.map((b: any, i: number) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: i < backups.backups.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none', fontSize: 13 }}>
            <span>{b.file}</span>
            <span style={{ color: '#8888a0' }}>{(b.size_bytes / 1024).toFixed(1)}KB</span>
            <span style={{ color: '#8888a0' }}>{b.created}</span>
          </div>
        )) : <p style={{ color: '#8888a0', fontSize: 13 }}>No backups yet</p>}
      </div>
    </div>
  );
}
