import { api, setToken, getBaseUrl } from './client'

// ── Auth ──
export interface LoginRequest { username: string; password: string }
export interface LoginResponse { access_token: string; token_type: string }
export async function login(req: LoginRequest): Promise<LoginResponse> {
  const res = await fetch(`${getBaseUrl()}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: req.username, password: req.password }),
  })
  const data = await res.json()
  if (res.ok) { setToken(data.access_token); return data }
  throw new Error(data.detail || 'Login failed')
}

// ── Dashboard ──
export interface DashboardMetrics {
  total_workers: number; online_workers: number; total_jobs: number
  active_jobs: number; queued_jobs: number; repositories: number
  workflows: number; ai_sessions: number; plugins: number
  system_health: string; queue_depth: number
}
export const fetchDashboard = () => api.get<DashboardMetrics>('/api/v1/dashboard')

// ── Workers ──
export interface Worker {
  id: string; name: string; status: string; hostname: string; ip_address: string
  cpu_percent: number; memory_percent: number; memory_used_gb: number
  disk_percent: number; temperature: number | null; last_seen: string
  current_jobs: number; version: string; latency_ms: number
}
export const fetchWorkers = () => api.get<Worker[]>('/api/v1/workers')
export const fetchWorker = (id: string) => api.get<Worker>(`/api/v1/workers/${id}`)
export const pauseWorker = (id: string) => api.post(`/api/v1/workers/${id}/pause`)
export const resumeWorker = (id: string) => api.post(`/api/v1/workers/${id}/resume`)
export const deleteWorker = (id: string) => api.delete(`/api/v1/workers/${id}`)
export const restartWorker = async (id: string) => {
  await api.post(`/api/v1/workers/${id}/pause`)
  await new Promise(r => setTimeout(r, 1000))
  return api.post(`/api/v1/workers/${id}/resume`)
}

// ── Jobs ──
export interface Job {
  id: string; name: string; type: string; status: string; priority: number
  progress: number; worker_id: number | null; created_at: string
  started_at: string | null; completed_at: string | null; result: any
  handler: string; params: any
}
export const fetchJobs = (params?: { status?: string; limit?: number }) =>
  api.get<Job[]>(`/api/v1/jobs?${new URLSearchParams(params as any).toString()}`)

// ── Health ──
export interface HealthStatus {
  status: string; version: string; database: string; uptime_seconds: number
  worker_count: number; services: Record<string, string>
}
export const fetchHealth = () => api.get<HealthStatus>('/api/v1/health')

// ── Repositories ──
export interface Repository {
  id: string; name: string; path: string; status: string; language: string
  total_files: number; indexed_files: number; last_indexed: string | null
  branches: number; symbols: number
}
export const fetchRepositories = () => api.get<Repository[]>('/api/v1/repositories')

// ── Workflows ──
export interface Workflow {
  id: string; name: string; status: string; created_at: string
  updated_at: string; task_count: number; completed_tasks: number
}
export const fetchWorkflows = () => api.get<Workflow[]>('/api/v1/workflows')

// ── AI ──
export interface AIModel {
  name: string; provider: string; status: string; memory_usage_mb: number
  context_length: number; quantization: string; loaded: boolean
}
export const fetchAIModels = () => api.get<AIModel[]>('/api/v1/ai/models')
export const fetchAISessions = () => api.get<any[]>('/api/v1/ai/sessions')

// ── Plugins ──
export interface Plugin {
  id: string; name: string; version: string; author: string; description: string
  enabled: boolean; permissions: string[]; hooks: string[]
  installed_at: string; status: string
}
export const fetchPlugins = () => api.get<Plugin[]>('/api/v1/plugins')
export const enablePlugin = (id: string) => api.post(`/api/v1/plugins/${id}/enable`)
export const disablePlugin = (id: string) => api.post(`/api/v1/plugins/${id}/disable`)
export const uninstallPlugin = (id: string) => api.delete(`/api/v1/plugins/${id}`)

// ── Production / Diagnostics ──
export interface DiagnosticCheck {
  name: string; status: string; detail?: string; latency_ms?: number
}
export const fetchDiagnostics = () =>
  api.get<DiagnosticCheck[]>('/api/v1/production/health')

export interface SystemMetrics {
  cpu_percent: number; memory_percent: number; memory_used_gb: number
  memory_total_gb: number; disk_percent: number; network_mbps: number
  queue_depth: number; active_sessions: number
}
export const fetchSystemMetrics = () =>
  api.get<SystemMetrics>('/api/v1/production/monitoring')

// ── Audit / Logs ──
export interface LogEntry {
  timestamp: string; level: string; logger: string; message: string
}
export const fetchLogs = (params?: { level?: string; limit?: number; search?: string }) =>
  api.get<LogEntry[]>(`/api/v1/logs?${new URLSearchParams(params as any).toString()}`)

// ── Ollama / AI Providers (direct, not through master) ──
export async function fetchOllamaModels(host = '127.0.0.1', port = 11434): Promise<string[]> {
  try {
    const res = await fetch(`http://${host}:${port}/api/tags`, { signal: AbortSignal.timeout(3000) })
    if (!res.ok) return []
    const data = await res.json()
    return (data.models || []).map((m: any) => m.name)
  } catch { return [] }
}

export async function checkOllamaHealth(host = '127.0.0.1', port = 11434): Promise<boolean> {
  try {
    const res = await fetch(`http://${host}:${port}/api/tags`, { signal: AbortSignal.timeout(2000) })
    return res.ok
  } catch { return false }
}
