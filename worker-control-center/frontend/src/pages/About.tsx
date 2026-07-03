import { Cpu } from 'lucide-react';

export function AboutPage() {
  return (
    <div style={{ maxWidth: 500, margin: '0 auto', paddingTop: 40, textAlign: 'center' }}>
      <Cpu size={64} style={{ color: 'var(--accent)', marginBottom: 16 }} />
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>AICluster Worker Control Center</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>Version 1.0.0</p>

      <div className="card" style={{ textAlign: 'left', marginBottom: 16 }}>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: 14 }}>
          AICluster is a private AI compute platform that turns idle Windows PCs on a LAN
          into a unified compute cluster. No cloud, no subscriptions, no data leaving your network.
        </p>
      </div>

      <div className="card" style={{ textAlign: 'left', fontSize: 13 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Application</span>
          <span>Worker Control Center</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Version</span>
          <span>1.0.0</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Framework</span>
          <span>React + FastAPI</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Platform</span>
          <span>Windows (Tauri-ready)</span>
        </div>
      </div>
    </div>
  );
}
