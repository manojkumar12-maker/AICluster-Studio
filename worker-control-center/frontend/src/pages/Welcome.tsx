import { Play, Wrench, RotateCcw, LogOut, Cpu } from 'lucide-react';
import { useAppStore } from '../stores/app-store';

export function WelcomePage() {
  const setPage = useAppStore((s) => s.setPage);

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', paddingTop: 40 }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div style={{ fontSize: 48, marginBottom: 16, color: 'var(--accent)' }}>
          <Cpu size={64} style={{ display: 'inline' }} />
        </div>
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>AICluster Worker</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Control Center v1.0.0</p>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 8, maxWidth: 400, margin: '8px auto 0' }}>
          Install, configure, monitor and control your AICluster Worker node.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <button className="btn btn-primary" style={{ width: '100%', padding: 14, justifyContent: 'center', fontSize: 15 }} onClick={() => setPage('installation')}>
          <Play size={18} /> Install Worker
        </button>
        <button className="btn btn-secondary" style={{ width: '100%', padding: 14, justifyContent: 'center' }} onClick={() => setPage('diagnostics')}>
          <Wrench size={18} /> Repair Worker
        </button>
        <button className="btn btn-secondary" style={{ width: '100%', padding: 14, justifyContent: 'center' }}>
          <RotateCcw size={18} /> Update Worker
        </button>
        <button className="btn btn-secondary" style={{ width: '100%', padding: 14, justifyContent: 'center' }}>
          <LogOut size={18} /> Exit
        </button>
      </div>
    </div>
  );
}
