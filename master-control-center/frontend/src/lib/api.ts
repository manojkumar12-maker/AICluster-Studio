const API = 'http://127.0.0.1:8800/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) { const err = await res.text(); throw new Error(err || `HTTP ${res.status}`); }
  return res.json();
}

export const api = {
  clusterStatus: () => request<any>('/cluster/status'),
  clusterHealth: () => request<any>('/cluster/health'),
  clusterMap: () => request<any>('/cluster/map'),
  clusterWorkers: () => request<any>('/cluster/workers'),
  discovery: () => request<any>('/cluster/discovery'),
  scan: (network: string) => request<any>(`/cluster/discovery?network_range=${network}`, { method: 'POST' }),
  registerWorker: (data: any) => request<any>('/cluster/discovery/register', { method: 'POST', body: JSON.stringify(data) }),
  registerAll: () => request<any>('/cluster/discovery/register-all', { method: 'POST' }),
  setMaintenance: (workerId: string, enabled: boolean) => request<any>('/cluster/workers/maintenance', { method: 'POST', body: JSON.stringify({ worker_id: workerId, enabled }) }),
  backup: () => request<any>('/cluster/backup', { method: 'POST' }),
  restore: (path: string) => request<any>('/cluster/restore', { method: 'POST', body: JSON.stringify({ path }) }),
  listBackups: () => request<any>('/backups'),
  getAlerts: () => request<any>('/alerts'),
  markAlertsRead: () => request<any>('/alerts/read', { method: 'POST' }),
  diagnostics: () => request<any>('/diagnostics'),
  getLogs: (source?: string) => request<any>(`/logs?source=${source || ''}`),
  workerLogs: (id: string) => request<any>(`/workers/${id}/logs`),
  systemVersion: () => request<any>('/system/version'),
  health: () => request<any>('/health'),
};
