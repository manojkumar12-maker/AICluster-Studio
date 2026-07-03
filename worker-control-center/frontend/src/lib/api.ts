const API = 'http://127.0.0.1:8900/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

export interface StatusData {
  worker_id: string | null;
  worker_name: string;
  status: string;
  version: string;
  master_url: string | null;
  cpu_percent: number;
  ram_percent: number;
  disk_percent: number;
  uptime_seconds: number;
  jobs_completed: number;
  jobs_failed: number;
  current_job: string | null;
  heartbeat_status: string;
  last_heartbeat: string | null;
  is_paused: boolean;
  connection_quality: string;
}

export interface ConfigData {
  master_url: string;
  worker_name: string;
  heartbeat_interval: number;
  poll_interval: number;
  log_level: string;
  version: string;
  worker_description: string;
  auto_start: boolean;
  launch_with_windows: boolean;
  auto_reconnect: boolean;
}

export interface SystemInfo {
  os: string;
  os_version: string;
  python_version: string;
  python_path: string;
  git_installed: boolean;
  disk_free_gb: number;
  disk_total_gb: number;
  ram_total_gb: number;
  ram_free_gb: number;
  cpu_count: number;
  cpu_percent: number;
  is_admin: boolean;
  worker_folder_exists: boolean;
  log_folder_exists: boolean;
  has_permissions: boolean;
  master_online: boolean;
}

export interface ConnectionTest {
  ping: string;
  rest_api: string;
  websocket: string;
  auth: string;
  worker_registration: string;
  average_latency_ms: number;
  packet_loss_percent: number;
  master_version: string | null;
  worker_id: string | null;
  details: string;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  source: string;
}

export interface ActionResult {
  success: boolean;
  message: string;
}

export const api = {
  getStatus: () => request<StatusData>('/status'),
  getConfig: () => request<ConfigData>('/config'),
  updateConfig: (data: Partial<ConfigData>) => request<ActionResult>('/config', { method: 'POST', body: JSON.stringify(data) }),
  resetConfig: () => request<ActionResult>('/config/reset', { method: 'POST' }),
  startWorker: () => request<ActionResult>('/start', { method: 'POST' }),
  stopWorker: () => request<ActionResult>('/stop', { method: 'POST' }),
  restartWorker: () => request<ActionResult>('/restart', { method: 'POST' }),
  registerWorker: () => request<ActionResult>('/register', { method: 'POST' }),
  testConnection: (masterUrl?: string) => request<ConnectionTest>('/test-connection', {
    method: 'POST',
    body: JSON.stringify(masterUrl ? { master_url: masterUrl } : {}),
  }),
  getLogs: (limit?: number) => request<LogEntry[]>(`/logs?limit=${limit || 100}`),
  exportLogs: () => request<ActionResult>('/logs/export', { method: 'POST' }),
  clearLogs: () => request<ActionResult>('/logs/clear', { method: 'POST' }),
  getSystemInfo: () => request<SystemInfo>('/system-info'),
  getInstallSteps: () => request<{ step: string; status: string; message: string }[]>('/install/steps'),
  runInstall: () => request<ActionResult>('/install/run', { method: 'POST' }),
  health: () => request<{ status: string }>('/health'),
};
