import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Search, Download, Trash2, RefreshCw } from 'lucide-react';
import { api, type LogEntry } from '../lib/api';

export function LogsPage() {
  const [filter, setFilter] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const logEndRef = useRef<HTMLDivElement>(null);
  const { data: logs, refetch, isLoading } = useQuery<LogEntry[]>({
    queryKey: ['logs', filter],
    queryFn: () => api.getLogs(500),
    refetchInterval: 5000,
  });

  const exportMutation = useMutation({ mutationFn: api.exportLogs });
  const clearMutation = useMutation({ mutationFn: api.clearLogs });

  useEffect(() => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const filtered = logs?.filter((l) =>
    !filter || l.level.includes(filter) || l.message.toLowerCase().includes(filter.toLowerCase())
  ) || [];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Logs</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Worker activity log</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={() => refetch()}><RefreshCw size={16} /></button>
          <button className="btn btn-secondary" onClick={() => exportMutation.mutate()}><Download size={16} /> Export</button>
          <button className="btn btn-secondary" onClick={() => { clearMutation.mutate(); setTimeout(refetch, 500); }}><Trash2 size={16} /> Clear</button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={16} style={{ position: 'absolute', left: 10, top: 12, color: 'var(--text-secondary)' }} />
          <input style={{ paddingLeft: 32 }} placeholder="Search logs..." value={filter} onChange={(e) => setFilter(e.target.value)} />
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', whiteSpace: 'nowrap' }}>
          <input type="checkbox" checked={autoScroll} onChange={() => setAutoScroll(!autoScroll)} style={{ width: 'auto' }} />
          Auto-scroll
        </label>
      </div>

      <div className="card" style={{ flex: 1, overflow: 'auto', fontFamily: 'monospace', fontSize: 12 }}>
        {isLoading && <p style={{ color: 'var(--text-secondary)', padding: 16 }}>Loading logs...</p>}
        {!isLoading && filtered.length === 0 && <p style={{ color: 'var(--text-secondary)', padding: 16 }}>No log entries found.</p>}
        {filtered.map((log, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, padding: '3px 8', borderRadius: 4, background: i % 2 === 0 ? 'rgba(0,0,0,0.1)' : 'transparent' }}>
            <span style={{ color: 'var(--text-secondary)', width: 80, flexShrink: 0 }}>{log.timestamp}</span>
            <span style={{
              width: 60, flexShrink: 0,
              color: log.level === 'ERROR' ? 'var(--error)' : log.level === 'WARNING' ? 'var(--warning)' : 'var(--accent)',
            }}>{log.level}</span>
            <span style={{ color: 'var(--text-primary)', flex: 1 }}>{log.message}</span>
          </div>
        ))}
        <div ref={logEndRef} />
      </div>

      <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>
        {filtered.length} entries {filter ? `(filtered)` : ''}
      </p>
    </div>
  );
}
