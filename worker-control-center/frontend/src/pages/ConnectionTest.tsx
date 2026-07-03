import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Check, X, Loader, Zap } from 'lucide-react';
import { api, type ConnectionTest } from '../lib/api';

export function ConnectionTestPage() {
  const [masterUrl, setMasterUrl] = useState('http://localhost:8000');

  const testMutation = useMutation<ConnectionTest>({
    mutationFn: () => api.testConnection(masterUrl),
  });

  const results = testMutation.data ? [
    { label: 'Ping Master', status: testMutation.data.ping },
    { label: 'REST API', status: testMutation.data.rest_api },
    { label: 'Authentication', status: testMutation.data.auth },
    { label: 'Worker Registration', status: testMutation.data.worker_registration },
  ] : [];

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Connection Test</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>Verify connectivity to your Master server</p>

      <div className="card" style={{ marginBottom: 20 }}>
        <label>Master Server URL</label>
        <div style={{ display: 'flex', gap: 8 }}>
          <input value={masterUrl} onChange={(e) => setMasterUrl(e.target.value)} placeholder="http://localhost:8000" />
          <button className="btn btn-primary" onClick={() => testMutation.mutate()} disabled={testMutation.isPending} style={{ width: 120 }}>
            {testMutation.isPending ? <><Loader size={16} style={{ animation: 'spin 1s linear infinite' }} /> Testing</> : <><Zap size={16} /> Test</>}
          </button>
        </div>
      </div>

      {testMutation.isPending && (
        <div className="card" style={{ textAlign: 'center', padding: 40 }}>
          <Loader size={32} style={{ color: 'var(--accent)', animation: 'spin 1s linear infinite', marginBottom: 12 }} />
          <p>Running connection tests...</p>
        </div>
      )}

      {testMutation.data && (
        <>
          <div className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Test Results</h3>
            {results.map((r, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: i < results.length - 1 ? '1px solid var(--border-color)' : 'none' }}>
                {r.status === 'pass' ? <Check size={16} style={{ color: 'var(--success)' }} /> : <X size={16} style={{ color: 'var(--error)' }} />}
                <span style={{ flex: 1, fontSize: 14 }}>{r.label}</span>
                <span className={`badge ${r.status === 'pass' ? 'badge-success' : 'badge-error'}`}>{r.status.toUpperCase()}</span>
              </div>
            ))}
          </div>

          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Network Metrics</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Average Latency</p>
                <p style={{ fontSize: 18, fontWeight: 700 }}>{testMutation.data.average_latency_ms.toFixed(1)} ms</p>
              </div>
              <div>
                <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Packet Loss</p>
                <p style={{ fontSize: 18, fontWeight: 700 }}>{testMutation.data.packet_loss_percent.toFixed(1)}%</p>
              </div>
              <div>
                <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Master Version</p>
                <p style={{ fontSize: 14 }}>{testMutation.data.master_version || 'Unknown'}</p>
              </div>
              <div>
                <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Worker ID</p>
                <p style={{ fontSize: 14 }}>{(testMutation.data.worker_id || 'Not registered').slice(0, 20)}</p>
              </div>
            </div>
          </div>
        </>
      )}

      {testMutation.isError && (
        <div className="card" style={{ borderColor: 'var(--error)' }}>
          <p style={{ color: 'var(--error)' }}>Connection failed: {testMutation.error.message}</p>
        </div>
      )}
    </div>
  );
}
