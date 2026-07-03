import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Save, RotateCcw, RefreshCw } from 'lucide-react';
import { api, type ConfigData } from '../lib/api';

export function ConfigurationPage() {
  const { data: config, refetch } = useQuery<ConfigData>({ queryKey: ['config'], queryFn: api.getConfig });
  const [form, setForm] = useState<ConfigData | null>(null);

  useEffect(() => { if (config && !form) setForm(config); }, [config, form]);

  const saveMutation = useMutation({
    mutationFn: (data: Partial<ConfigData>) => api.updateConfig(data),
    onSuccess: () => refetch(),
  });

  const resetMutation = useMutation({
    mutationFn: () => api.resetConfig(),
    onSuccess: () => { refetch(); setForm(null); },
  });

  return (
    <div style={{ maxWidth: 700, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Configuration</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Worker settings</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={() => resetMutation.mutate()}><RotateCcw size={16} /> Reset</button>
          <button className="btn btn-secondary" onClick={() => refetch()}><RefreshCw size={16} /></button>
        </div>
      </div>

      {form && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Connection</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div>
                <label>Master URL</label>
                <input value={form.master_url} onChange={(e) => setForm({ ...form, master_url: e.target.value })} placeholder="http://localhost:8000" />
              </div>
              <div>
                <label>Worker Name</label>
                <input value={form.worker_name} onChange={(e) => setForm({ ...form, worker_name: e.target.value })} placeholder="Auto (hostname)" />
              </div>
              <div>
                <label>Heartbeat Interval (s)</label>
                <input type="number" value={form.heartbeat_interval} onChange={(e) => setForm({ ...form, heartbeat_interval: parseInt(e.target.value) || 5 })} />
              </div>
              <div>
                <label>Poll Interval (s)</label>
                <input type="number" value={form.poll_interval} onChange={(e) => setForm({ ...form, poll_interval: parseInt(e.target.value) || 5 })} />
              </div>
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Advanced</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div>
                <label>Log Level</label>
                <select value={form.log_level} onChange={(e) => setForm({ ...form, log_level: e.target.value })}>
                  <option>DEBUG</option>
                  <option>INFO</option>
                  <option>WARNING</option>
                  <option>ERROR</option>
                </select>
              </div>
              <div>
                <label>Description</label>
                <input value={form.worker_description} onChange={(e) => setForm({ ...form, worker_description: e.target.value })} placeholder="Optional description" />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 24, marginTop: 16 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input type="checkbox" checked={form.auto_start} onChange={(e) => setForm({ ...form, auto_start: e.target.checked })} style={{ width: 'auto' }} />
                Auto Start
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input type="checkbox" checked={form.auto_reconnect} onChange={(e) => setForm({ ...form, auto_reconnect: e.target.checked })} style={{ width: 'auto' }} />
                Auto Reconnect
              </label>
            </div>
          </div>

          <button className="btn btn-primary" style={{ alignSelf: 'flex-start' }} onClick={() => saveMutation.mutate(form)} disabled={saveMutation.isPending}>
            <Save size={16} /> {saveMutation.isPending ? 'Saving...' : 'Save Configuration'}
          </button>

          {saveMutation.isSuccess && <p style={{ color: 'var(--success)', fontSize: 13 }}>Configuration saved successfully</p>}
          {saveMutation.isError && <p style={{ color: 'var(--error)', fontSize: 13 }}>Failed to save: {saveMutation.error.message}</p>}
        </div>
      )}
    </div>
  );
}
