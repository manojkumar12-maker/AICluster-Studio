import { Cpu } from 'lucide-react';
export function AboutPage() {
  return (
    <div style={{ maxWidth: 500, margin: '0 auto', paddingTop: 40, textAlign: 'center' }}>
      <Cpu size={64} style={{ color: '#6366f1', marginBottom: 16 }} />
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>AICluster Master Control Center</h1>
      <p style={{ color: '#8888a0', marginBottom: 24 }}>Version 1.0.0</p>
      <div className="card" style={{ textAlign: 'left', marginBottom: 16 }}>
        <p style={{ color: '#8888a0', lineHeight: 1.6, fontSize: 14 }}>AICluster turns idle Windows PCs on a LAN into a unified compute cluster. No cloud, no subscriptions.</p>
      </div>
      <div className="card" style={{ textAlign: 'left', fontSize: 13 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}><span style={{ color: '#8888a0' }}>Application</span><span>Master Control Center</span></div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}><span style={{ color: '#8888a0' }}>Version</span><span>1.0.0</span></div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}><span style={{ color: '#8888a0' }}>Framework</span><span>React + FastAPI</span></div>
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}><span style={{ color: '#8888a0' }}>Phase</span><span>3.5 (Cluster Operations)</span></div>
      </div>
    </div>
  );
}
