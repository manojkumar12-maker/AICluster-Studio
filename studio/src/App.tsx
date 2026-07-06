import { useEffect, useState, useCallback, useRef } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { setOnAuthFailure } from './api/client'
import { useAuthStore } from './stores/authStore'
import { useBackend, useHealthCheck, useLoginForm } from './hooks/useBackend'
import {
  fetchDashboard, fetchWorkers, fetchJobs, fetchHealth,
  fetchRepositories, fetchWorkflows,
  fetchAIModels, fetchPlugins,
  fetchDiagnostics, fetchSystemMetrics, fetchLogs,
  pauseWorker, resumeWorker, deleteWorker, restartWorker,
  enablePlugin, disablePlugin, uninstallPlugin,
  type Worker, type Job, type Repository, type Workflow,
  type AIModel, type Plugin, type DiagnosticCheck,
  type LogEntry,
} from './api/endpoints'

type NavPage = 'dashboard' | 'workers' | 'models' | 'plugins' | 'repository' | 'workflows' | 'performance' | 'diagnostics' | 'settings' | 'logs'

// ── Offline Banner ──
function OfflineBanner({ onRetry }: { onRetry: () => void }) {
  return (<div className="offline-banner"><span>⚠️ Backend unavailable. Retrying automatically...</span><button className="btn-small" onClick={onRetry}>Retry Now</button></div>)
}

// ── Loading Skeleton ──
function SkeletonCard() {
  return (<div className="skeleton-card"><div className="skeleton-line w-60" /><div className="skeleton-line w-80" /><div className="skeleton-line w-40" /></div>)
}

// ── Error Dialog ──
function ErrorBox({ error, onRetry }: { error: string; onRetry?: () => void }) {
  return (<div className="error-box"><span>⚠️ {error}</span>{onRetry && <button className="btn-small" onClick={onRetry}>Retry</button>}</div>)
}

// ── Confirm Dialog ──
function ConfirmDialog({ title, message, onConfirm, onCancel }: { title: string; message: string; onConfirm: () => void; onCancel: () => void }) {
  return (<div className="dialog-overlay" onClick={onCancel}><div className="dialog" onClick={e => e.stopPropagation()}><h3>{title}</h3><p>{message}</p><div className="dialog-actions"><button className="btn-secondary" onClick={onCancel}>Cancel</button><button className="btn-danger" onClick={onConfirm}>Confirm</button></div></div></div>)
}

// ── Login Screen ──
function LoginScreen() {
  const [connecting, setConnecting] = useState(true)
  const [connError, setConnError] = useState<string | null>(null)
  const [startingMaster, setStartingMaster] = useState(false)
  const { username, setUsername, password, setPassword, error, loading, submit } = useLoginForm()
  const connectingRef = useRef(true)

  const checkHealth = useCallback(() => {
    fetch('http://127.0.0.1:8000/api/v1/health', { signal: AbortSignal.timeout(5000) })
      .then(r => { if (r.ok) { setConnecting(false); setConnError(null); connectingRef.current = false } })
      .catch(() => { if (connectingRef.current) setConnError('Master is not available') })
  }, [])

  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 3000)
    return () => clearInterval(interval)
  }, [checkHealth])

  const startMaster = useCallback(() => {
    setStartingMaster(true)
    setConnError(null)
    invoke('startup_services').then(() => {
      setStartingMaster(false)
    }, (e: any) => {
      setStartingMaster(false)
      setConnError('Failed to start Master: ' + (typeof e === 'string' ? e : 'Unknown error'))
    })
  }, [])

  return (<div className="login-screen"><div className="login-card"><div className="login-logo"><svg width="48" height="48" viewBox="0 0 64 64" fill="none"><rect width="64" height="64" rx="14" fill="#4c6ef5" /><text x="32" y="44" textAnchor="middle" fill="white" fontSize="28" fontFamily="monospace" fontWeight="bold">AI</text></svg></div><h2>Sign In</h2>{connecting ? <><p className="login-sub">Connecting to AICluster Master...</p><div className="splash-progress-bar" style={{margin: '16px auto', width: 200}}><div className="splash-progress-fill" style={{width: '60%'}} /></div>{connError && !startingMaster && <><p className="login-sub" style={{color:'var(--warning)'}}>{connError}</p><button className="btn-secondary" style={{marginTop: 12}} onClick={startMaster}>Start Master</button></>}{startingMaster && <p className="login-sub" style={{marginTop: 12}}>Starting Master Server...</p>}</> : <><p className="login-sub">Enter your AICluster admin credentials</p><div className="form-group"><label>Username</label><input value={username} onChange={e => setUsername(e.target.value)} /></div><div className="form-group"><label>Password</label><input type="password" value={password} onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === 'Enter' && submit()} /></div>{error && <div className="login-error">{error}</div>}<button className="btn-primary btn-full" onClick={submit} disabled={loading}>{loading ? 'Signing in...' : 'Sign In'}</button></>}</div></div>)
}

// ── Dashboard Page ──
function DashboardPage() {
  const dash = useBackend(fetchDashboard, [], 5000)
  const health = useBackend(fetchHealth, [], 10000)
  const workers = useBackend(fetchWorkers, [], 10000)
  const jobs = useBackend(() => fetchJobs({ limit: 50 }), [], 10000)

  if (dash.error && !dash.data) return <ErrorBox error={dash.error} onRetry={dash.refresh} />
  if (!dash.data) return <div className="page-content"><div className="stats-grid"><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></div></div>

  const d = dash.data
  const healthy = health.data?.status === 'healthy'
  return (<div className="page-content"><div className="page-header"><h2>Dashboard</h2><span className={`cluster-badge ${healthy ? 'healthy' : 'degraded'}`}>{healthy ? 'All Systems Operational' : 'Degraded'}</span></div><div className="stats-grid">{[
    { label: 'Workers', value: `${d.online_workers}/${d.total_workers}`, icon: '⚡', status: d.online_workers > 0 ? 'running' : 'stopped' },
    { label: 'Jobs', value: String(d.active_jobs), icon: '📋', status: 'running', sub: `${d.queued_jobs} queued` },
    { label: 'Repositories', value: String(d.repositories), icon: '📁', status: 'running' },
    { label: 'Plugins', value: String(d.plugins), icon: '🧩', status: 'running' },
    { label: 'Queue Depth', value: String(d.queue_depth), icon: '📊', status: d.queue_depth > 0 ? 'running' : 'stopped' },
    { label: 'Workflows', value: String(d.workflows), icon: '🔀', status: d.workflows > 0 ? 'running' : 'stopped' },
  ].map(s => (<div key={s.label} className={`stat-card ${s.status}`}><div className="stat-icon">{s.icon}</div><div className="stat-info"><span className="stat-value">{s.value}</span><span className="stat-label">{s.label}</span>{s.sub && <span className="stat-sub">{s.sub}</span>}</div></div>))}</div><div className="card"><h3>Recent Workers</h3><div className="service-list">{(workers.data || []).slice(0, 5).map((w: Worker) => (<div key={w.id} className="service-item"><span className={`status-dot ${w.status === 'online' ? 'running' : 'stopped'}`} /><span>{w.name}</span><span className="service-pid">{w.ip_address}</span><span className="service-uptime">{w.cpu_percent}% CPU</span></div>))}{(workers.data || []).length === 0 && <div className="empty-state">No workers connected</div>}</div></div><div className="card"><h3>Recent Jobs</h3><div className="service-list">{(jobs.data || []).slice(0, 5).map((j: Job) => (<div key={j.id} className="service-item"><span className={`status-dot ${j.status === 'completed' ? 'running' : j.status === 'failed' ? 'error' : 'checking'}`} /><span>{j.name}</span><span className="service-pid">{j.handler}</span><span className="service-uptime">{j.status}</span></div>))}{(jobs.data || []).length === 0 && <div className="empty-state">No jobs yet</div>}</div></div></div>)
}

// ── Workers Page ──
function WorkersPage() {
  const { data: workers, loading, error, refresh } = useBackend(fetchWorkers, [], 5000)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [confirmId, setConfirmId] = useState<string | null>(null)
  const [confirmAction, setConfirmAction] = useState<string>('')

  const doAction = useCallback(async (id: string, action: string) => {
    try {
      if (action === 'pause') await pauseWorker(id)
      else if (action === 'resume') await resumeWorker(id)
      else if (action === 'restart') await restartWorker(id)
      else if (action === 'delete') await deleteWorker(id)
      refresh()
    } catch (err: any) { alert(`Action failed: ${err.message}`) }
    setConfirmId(null)
  }, [refresh])

  const filtered = (workers || []).filter((w: Worker) =>
    (filter === 'all' || w.status === filter) &&
    w.name.toLowerCase().includes(search.toLowerCase())
  )

  if (error && !workers) return <div className="page-content"><ErrorBox error={error} onRetry={refresh} /></div>

  function renderActions(w: Worker) {
    if (w.status === 'online' || w.status === 'idle') {
      return <span><button className="btn-small" title="Pause" onClick={() => { setConfirmId(w.id); setConfirmAction('pause') }}>P</button><button className="btn-small" title="Restart" onClick={() => doAction(w.id, 'restart')}>R</button></span>
    } else if (w.status === 'offline') {
      return <button className="btn-small" title="Remove" onClick={() => { setConfirmId(w.id); setConfirmAction('delete') }}>X</button>
    }
    return <button className="btn-small" title="Resume" onClick={() => doAction(w.id, 'resume')}>R</button>
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <h2>Worker Manager</h2>
        <div className="header-actions">
          <select className="select-input" value={filter} onChange={e => setFilter(e.target.value)}>
            <option value="all">All ({workers?.length || 0})</option>
            <option value="online">Online</option>
            <option value="idle">Idle</option>
            <option value="offline">Offline</option>
          </select>
          <input className="search-input" placeholder="Search workers..." value={search} onChange={e => setSearch(e.target.value)} />
          <button className="btn-secondary" onClick={refresh}>Refresh</button>
        </div>
      </div>
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Worker</th><th>Status</th><th>IP</th><th>CPU</th><th>RAM</th>
              <th>Latency</th><th>Jobs</th><th>Last Seen</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && workers?.length === 0 ? (
              <tr><td colSpan={9}><div className="loading-state">Loading...</div></td></tr>
            ) : filtered.map((w: Worker) => (
              <tr key={w.id}>
                <td><span className="worker-name">{w.name}</span></td>
                <td><span className={'status-badge ' + w.status}>{w.status}</span></td>
                <td><code>{w.ip_address}</code></td>
                <td><div className="progress-bar"><div className="progress-fill cpu" style={{ width: w.cpu_percent + '%' }} /></div><span className="progress-label">{w.cpu_percent}%</span></td>
                <td>{w.memory_used_gb?.toFixed(1) || '-'} GB</td>
                <td>{w.latency_ms || '-'}ms</td>
                <td>{w.current_jobs || 0}</td>
                <td>{w.last_seen ? new Date(w.last_seen).toLocaleTimeString() : '-'}</td>
                <td>
                  <div className="action-buttons">
                    {renderActions(w)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {confirmId !== null && (
        <ConfirmDialog
          title={confirmAction === 'delete' ? 'Remove Worker' : confirmAction === 'pause' ? 'Pause Worker' : 'Resume Worker'}
          message={confirmAction === 'delete' ? 'Remove this worker from the cluster?' : confirmAction === 'pause' ? 'Pause this worker?' : 'Resume this worker?'}
          onConfirm={() => doAction(confirmId, confirmAction)}
          onCancel={() => setConfirmId(null)}
        />
      )}
    </div>
  )
}

// ── Models Page ──
function ModelsPage() {
  const ai = useBackend(fetchAIModels, [], 10000)
  return (<div className="page-content"><div className="page-header"><h2>AI Model Manager</h2><button className="btn-secondary" onClick={ai.refresh}>[~] Refresh</button></div>{ai.error && !ai.data ? <ErrorBox error={ai.error} onRetry={ai.refresh} /> : ai.loading && !ai.data ? <div className="loading-state">Loading models...</div> : <div className="provider-grid">{(ai.data || []).length === 0 ? <div className="card"><p className="text-muted">No AI models detected. Install Ollama or llama.cpp to get started.</p></div> : (ai.data || []).map((m: AIModel) => (<div key={m.name} className={`provider-card-lg ${m.loaded ? 'installed' : ''}`}><div className="provider-card-header"><h3>{m.name}</h3><span className={`status-badge ${m.loaded ? 'online' : 'offline'}`}>{m.loaded ? 'Loaded' : 'Unloaded'}</span></div><div className="provider-card-body"><p>Provider: <code>{m.provider}</code></p><p>Memory: {m.memory_usage_mb} MB</p><p>Context: {m.context_length} tokens</p>{m.quantization && <p>Quantization: {m.quantization}</p>}</div><div className="provider-card-footer"><button className="btn-primary btn-small">{m.loaded ? 'Unload' : 'Load'}</button><button className="btn-secondary btn-small">Verify</button></div></div>))}</div>}</div>)
}

// ── Plugins Page ──
function PluginsPage() {
  const { data: plugins, loading, error, refresh } = useBackend(fetchPlugins, [], 10000)
  const [confirmId, setConfirmId] = useState<string | null>(null)
  const [confirmAction, setConfirmAction] = useState('')

  const doAction = useCallback(async (id: string, action: string) => {
    try {
      if (action === 'enable') await enablePlugin(id)
      else if (action === 'disable') await disablePlugin(id)
      else if (action === 'uninstall') await uninstallPlugin(id)
      refresh()
    } catch (err: any) { alert(`Failed: ${err.message}`) }
    setConfirmId(null)
  }, [refresh])

  if (error && !plugins) return <div className="page-content"><ErrorBox error={error} onRetry={refresh} /></div>
  return (<div className="page-content"><div className="page-header"><h2>Plugin Center</h2><div className="header-actions"><button className="btn-secondary" onClick={refresh}>[~] Refresh</button></div></div>{loading && !plugins ? <div className="loading-state">Loading plugins...</div> : <div className="provider-grid">{(plugins || []).length === 0 ? <div className="card"><p className="text-muted">No plugins installed. Install plugins to extend functionality.</p></div> : (plugins || []).map((p: Plugin) => (<div key={p.id} className={`provider-card-lg ${p.enabled ? 'installed' : ''}`}><div className="provider-card-header"><h3>{p.name}</h3><span className={`status-badge ${p.enabled ? 'online' : 'offline'}`}>{p.enabled ? 'Enabled' : 'Disabled'}</span></div><div className="provider-card-body"><p>Version: {p.version} | Author: {p.author}</p><p>Permissions: {(p.permissions || []).join(', ') || 'None'}</p><p>Hooks: {(p.hooks || []).join(', ') || 'None'}</p></div><div className="provider-card-footer">{p.enabled ? <button className="btn-secondary btn-small" onClick={() => { setConfirmId(p.id); setConfirmAction('disable') }}>Disable</button> : <button className="btn-primary btn-small" onClick={() => { setConfirmId(p.id); setConfirmAction('enable') }}>Enable</button>}<button className="btn-danger btn-small" onClick={() => { setConfirmId(p.id); setConfirmAction('uninstall') }}>Uninstall</button></div></div>))}</div>}{confirmId !== null && <ConfirmDialog title={`${confirmAction} Plugin`} message={`Are you sure you want to ${confirmAction} this plugin?`} onConfirm={() => doAction(confirmId, confirmAction)} onCancel={() => setConfirmId(null)} />}</div>)
}

// ── Repository Page ──
function RepositoryPage() {
  const { data: repos, loading, error, refresh } = useBackend(fetchRepositories, [], 15000)
  if (error && !repos) return <div className="page-content"><ErrorBox error={error} onRetry={refresh} /></div>
  return (<div className="page-content"><div className="page-header"><h2>Repository Explorer</h2><button className="btn-secondary" onClick={refresh}>[~] Refresh</button></div>{loading && !repos ? <div className="loading-state">Loading repositories...</div> : <div className="repo-list">{(repos || []).length === 0 ? <div className="empty-state-lg"><div className="empty-icon">📁</div><h3>No Repositories</h3><p>Add a repository to start analyzing your codebase.</p></div> : (repos || []).map((r: Repository) => (<div key={r.id} className="repo-card"><div className="repo-header"><span className="repo-icon">📁</span><div><span className="repo-name">{r.name}</span><span className="repo-path">{r.path}</span></div><span className={`status-badge ${r.status === 'indexed' ? 'online' : r.status === 'indexing' ? 'idle' : 'offline'}`}>{r.status}</span></div><div className="repo-stats"><span>{r.total_files} files ({r.indexed_files} indexed)</span><span>{r.language}</span><span>{r.branches} branches</span><span>{r.symbols} symbols</span></div></div>))}</div>}</div>)
}

// ── Workflows Page ──
function WorkflowsPage() {
  const { data: workflows, loading, error, refresh } = useBackend(fetchWorkflows, [], 10000)
  if (error && !workflows) return <div className="page-content"><ErrorBox error={error} onRetry={refresh} /></div>
  return (<div className="page-content"><div className="page-header"><h2>Workflow Designer</h2><button className="btn-secondary" onClick={refresh}>[~] Refresh</button></div>{loading && !workflows ? <div className="loading-state">Loading workflows...</div> : <div className="repo-list">{(workflows || []).length === 0 ? <div className="empty-state-lg"><div className="empty-icon">🔀</div><h3>No Workflows</h3><p>Create automated workflows to chain AI operations and engineering tasks.</p></div> : (workflows || []).map((w: Workflow) => (<div key={w.id} className="repo-card"><div className="repo-header"><span className="repo-icon">🔀</span><div><span className="repo-name">{w.name}</span></div><span className={`status-badge ${w.status === 'completed' ? 'online' : w.status === 'running' ? 'idle' : 'offline'}`}>{w.status}</span></div><div className="repo-stats"><span>Tasks: {w.completed_tasks}/{w.task_count}</span><span>Created: {new Date(w.created_at).toLocaleDateString()}</span></div></div>))}</div>}</div>)
}

// ── Performance Page ──
function PerformancePage() {
  const { data: metrics, error, refresh } = useBackend(fetchSystemMetrics, [], 5000)
  if (error && !metrics) return <div className="page-content"><ErrorBox error={error} onRetry={refresh} /></div>
  if (!metrics) return <div className="page-content"><div className="metrics-grid"><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></div></div>
  return (<div className="page-content"><div className="page-header"><h2>Performance Dashboard</h2><span className="text-muted">Live • Updated every 5s</span></div><div className="metrics-grid">{[
    { label: 'CPU', value: `${metrics.cpu_percent}%`, color: '#22c55e' },
    { label: 'Memory', value: `${metrics.memory_used_gb.toFixed(1)} GB`, sub: `of ${metrics.memory_total_gb.toFixed(0)} GB`, color: '#4c6ef5' },
    { label: 'Disk', value: `${metrics.disk_percent}%`, color: '#f59e0b' },
    { label: 'Network', value: `${metrics.network_mbps} Mbps`, color: '#8b5cf6' },
    { label: 'Queue', value: String(metrics.queue_depth), color: '#ec4899' },
  ].map(m => (<div key={m.label} className="metric-card"><div className="metric-value" style={{ color: m.color }}>{m.value}</div><div className="metric-label">{m.label}</div>{m.sub && <div className="metric-sub">{m.sub}</div>}</div>))}</div></div>)
}

// ── Diagnostics Page ──
function DiagnosticsPage() {
  const { data: checks, loading, error, refresh } = useBackend(fetchDiagnostics, [], 15000)
  if (error && !checks) return <div className="page-content"><ErrorBox error={error} onRetry={refresh} /></div>
  return (<div className="page-content"><div className="page-header"><h2>Diagnostics Center</h2><button className="btn-secondary" onClick={refresh}>[~] Run All Checks</button></div>{loading && !checks ? <div className="loading-state">Running diagnostics...</div> : <div className="diagnostics-list">{(checks || []).length === 0 ? <div className="empty-state-lg"><div className="empty-icon">🔍</div><h3>No Diagnostics Data</h3></div> : (checks || []).map((c: DiagnosticCheck) => (<div key={c.name} className={`diagnostic-item ${c.status}`}><span className={`diag-icon ${c.status}`}>{c.status === 'healthy' ? '✓' : c.status === 'warning' ? '⚠' : '✗'}</span><span className="diag-name">{c.name}</span><span className="diag-status">{c.status}</span>{c.detail && <span className="diag-detail">{c.detail}</span>}</div>))}</div>}</div>)
}

// ── Logs Page ──
function LogsPage() {
  const { data: logs, loading, error, refresh } = useBackend(() => fetchLogs({ limit: 100 }), [], 5000)
  const [levelFilter, setLevelFilter] = useState('all')
  const filtered = (logs || []).filter((l: LogEntry) => levelFilter === 'all' || l.level === levelFilter)
  return (<div className="page-content"><div className="page-header"><h2>Logs</h2><div className="header-actions"><select className="select-input" value={levelFilter} onChange={e => setLevelFilter(e.target.value)}><option value="all">All Levels</option><option value="INFO">Info</option><option value="WARNING">Warning</option><option value="ERROR">Error</option><option value="DEBUG">Debug</option></select><button className="btn-secondary" onClick={refresh}>[~] Refresh</button></div></div>{error ? <ErrorBox error={error} onRetry={refresh} /> : <div className="log-container">{(filtered).length === 0 && !loading ? <div className="empty-state">No log entries</div> : filtered.map((l: LogEntry, i: number) => (<div key={i} className={`log-entry`}><span className="log-time">{l.timestamp}</span><span className={`log-level ${(l.level || 'info').toLowerCase()}`}>{l.level}</span><span className="log-logger">{l.logger}</span><span className="log-msg">{l.message}</span></div>))}</div>}</div>)
}

// ── Settings Page ──
function SettingsPage({ data, onSave, onNavigate }: { data: any; onSave: (d: any) => void; onNavigate: (p: NavPage) => void }) {
  const [tab, setTab] = useState('general')
  const [edit, setEdit] = useState(data)
  const tabs = [
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'appearance', label: 'Appearance', icon: '🎨' },
    { id: 'cluster', label: 'Cluster', icon: '🖥️' },
    { id: 'workers', label: 'Workers', icon: '⚡' },
    { id: 'models', label: 'AI Models', icon: '🤖' },
    { id: 'security', label: 'Security', icon: '🔒' },
    { id: 'performance', label: 'Performance', icon: '📊' },
    { id: 'network', label: 'Network', icon: '🌐' },
    { id: 'logs', label: 'Logs', icon: '📋' },
    { id: 'about', label: 'About', icon: 'ℹ️' },
  ]
  return (<div className="page-content"><div className="page-header"><h2>Settings</h2><div className="header-actions"><button className="btn-primary" onClick={() => { onSave(edit); onNavigate('dashboard') }}>Save Changes</button></div></div><div className="settings-layout"><div className="settings-sidebar">{tabs.map(t => (<button key={t.id} className={`settings-tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}><span>{t.icon}</span><span>{t.label}</span></button>))}</div><div className="settings-content">{tab === 'general' && <div className="settings-section"><h3>General</h3><div className="form-group"><label>Cluster Name</label><input value={edit.clusterName} onChange={e => setEdit({...edit, clusterName: e.target.value})} /></div><div className="form-row"><button className="btn-secondary">Export Config</button><button className="btn-secondary">Import Config</button><button className="btn-danger">Reset</button></div></div>}{tab === 'appearance' && <div className="settings-section"><h3>Appearance</h3><div className="form-group"><label>Theme</label><select className="select-input" style={{width:'100%'}}><option>Dark</option><option>Light</option></select></div></div>}{tab === 'cluster' && <div className="settings-section"><h3>Cluster</h3><div className="form-group"><label>Master Host</label><input value={edit.masterHost} onChange={e => setEdit({...edit, masterHost: e.target.value})} /></div><div className="form-group"><label>Master Port</label><input type="number" value={edit.masterPort} onChange={e => setEdit({...edit, masterPort: +e.target.value})} /></div></div>}{tab === 'about' && <div className="settings-section"><h3>About AICluster</h3><p>Version: 2.0.0</p><p>Backend: localhost:8000</p><p>Logged in as: {useAuthStore.getState().username || 'Not logged in'}</p></div>}</div></div></div>)
}

// ── Main App ──
function App() {
  const [phase, setPhase] = useState<'splash' | 'login' | 'app'>('splash')
  const [page, setPage] = useState<NavPage>('dashboard')
  const [setup, setSetup] = useState<any>({ clusterName: 'My Cluster', masterHost: '127.0.0.1', masterPort: 8000 })
  const { logout } = useAuthStore()
  const { healthy, checking, refresh: checkHealth } = useHealthCheck()

  // Handle auth failure
  useEffect(() => {
    setOnAuthFailure(() => { logout(); setPhase('login') })
  }, [logout])

  // Tauri navigate event
  useEffect(() => {
    const unlisten = listen<string>('navigate', (e) => setPage(e.payload as NavPage))
    return () => { unlisten.then(fn => fn()) }
  }, [])

  // Bootstrap
  useEffect(() => {
    const timer = setTimeout(() => {
      invoke<boolean>('is_configured').then(configured => {
        if (!configured) {
          // Auto-configure as standalone if no role set
          invoke('save_role', {
            role: 'standalone',
            settings: { master_host: '127.0.0.1', master_port: 8000, worker_port: 8001, worker_master_url: null, worker_name: null }
          }).then(() => {
            setSetup((p: any) => ({ ...p, role: 'standalone' }))
            invoke('startup_services').then(() => setPhase('login'), () => setPhase('login'))
          }, () => setPhase('login'))
        } else {
          invoke<string>('get_role').then(role => {
            setSetup((p: any) => ({ ...p, role }))
            invoke('startup_services').then(() => setPhase('login'), () => setPhase('login'))
          }, () => setPhase('login'))
        }
      }).catch(() => setPhase('login'))
    }, 1500)
    return () => clearTimeout(timer)
  }, [])

  const pages: { id: NavPage; label: string; icon: string }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'workers', label: 'Workers', icon: '⚡' },
    { id: 'models', label: 'AI Models', icon: '🤖' },
    { id: 'plugins', label: 'Plugins', icon: '🧩' },
    { id: 'repository', label: 'Repository', icon: '📁' },
    { id: 'workflows', label: 'Workflows', icon: '🔀' },
    { id: 'performance', label: 'Performance', icon: '📈' },
    { id: 'diagnostics', label: 'Diagnostics', icon: '🔍' },
    { id: 'logs', label: 'Logs', icon: '📋' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ]

  if (phase === 'splash') return (<div className="splash-screen"><div className="splash-content"><div className="splash-logo"><svg width="72" height="72" viewBox="0 0 64 64" fill="none"><rect width="64" height="64" rx="14" fill="#4c6ef5" /><text x="32" y="44" textAnchor="middle" fill="white" fontSize="28" fontFamily="monospace" fontWeight="bold">AI</text></svg></div><h1 className="splash-title">AICluster Studio</h1><p className="splash-version">v2.0.0</p><div className="splash-progress-bar"><div className="splash-progress-fill" style={{ width: '50%' }} /></div></div></div>)

  if (phase === 'login') return <LoginScreen />

  return (<div className="app-shell"><nav className="sidebar"><div className="sidebar-header"><div className="sidebar-logo"><svg width="28" height="28" viewBox="0 0 64 64" fill="none"><rect width="64" height="64" rx="12" fill="#4c6ef5" /><text x="32" y="44" textAnchor="middle" fill="white" fontSize="28" fontFamily="monospace" fontWeight="bold">AI</text></svg></div><span className="sidebar-title">AICluster</span><span className="sidebar-version">v2.0</span></div><div className="sidebar-nav">{pages.map(p => (<button key={p.id} className={`nav-item ${page === p.id ? 'active' : ''}`} onClick={() => setPage(p.id)}><span className="nav-icon">{p.icon}</span><span className="nav-label">{p.label}</span></button>))}</div><div className="sidebar-footer"><span className={`status-indicator ${healthy ? '' : 'error'}`} /><span className="sidebar-status">{checking ? 'Checking...' : healthy ? 'Connected' : 'Disconnected'}</span><button className="sidebar-logout" onClick={() => { logout(); setPhase('login') }} title="Sign out">🚪</button></div></nav><main className="main-area"><header className="topbar"><div className="topbar-left"><h1 className="topbar-title">{pages.find(p => p.id === page)?.label || 'Dashboard'}</h1></div><div className="topbar-right"><span className="role-badge">{setup.role || 'N/A'}</span><span className="text-muted">{useAuthStore.getState().username}</span></div></header>{!healthy && !checking && <OfflineBanner onRetry={checkHealth} />}<div className="content-area">{page === 'dashboard' && <DashboardPage />}{page === 'workers' && <WorkersPage />}{page === 'models' && <ModelsPage />}{page === 'plugins' && <PluginsPage />}{page === 'repository' && <RepositoryPage />}{page === 'workflows' && <WorkflowsPage />}{page === 'performance' && <PerformancePage />}{page === 'diagnostics' && <DiagnosticsPage />}{page === 'logs' && <LogsPage />}{page === 'settings' && <SettingsPage data={setup} onSave={(d: any) => setSetup(d)} onNavigate={setPage} />}</div></main></div>)
}

export default App
