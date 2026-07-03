export enum WorkerStatus {
  OFFLINE = "offline",
  ONLINE = "online",
  BUSY = "busy",
  PAUSED = "paused",
  ERROR = "error",
  DISABLED = "disabled",
  SHUTDOWN = "shutdown",
}

export enum JobStatus {
  QUEUED = "queued",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
  RETRYING = "retrying",
}

export enum JobPriority {
  LOW = 1,
  MEDIUM = 2,
  HIGH = 3,
  CRITICAL = 4,
}

export enum JobType {
  AI_CHAT = "ai_chat",
  CODE_ANALYSIS = "code_analysis",
  TESTING = "testing",
  DOCUMENTATION = "documentation",
  REFACTORING = "refactoring",
  FILE_PROCESSING = "file_processing",
  CUSTOM = "custom",
}

export enum UserRole {
  ADMIN = "admin",
  DEVELOPER = "developer",
  VIEWER = "viewer",
}

export interface HeartbeatData {
  worker_id: string;
  hostname: string;
  cpu_percent: number;
  ram_total: number;
  ram_used: number;
  disk_total: number;
  disk_used: number;
  temperature: number | null;
  network_rx: number;
  network_tx: number;
  status: WorkerStatus;
  current_job: string | null;
  uptime: number;
  version: string;
}

export interface WorkerRegister {
  hostname: string;
  ip_address: string;
  port: number;
  version: string;
  cpu_limit: number;
  ram_limit_gb: number;
}

export interface WorkerResponse {
  id: string;
  worker_name: string;
  hostname: string;
  ip: string;
  status: string;
  cpu_percent: number;
  ram_percent: number;
  disk_percent: number;
  temperature: number | null;
  network_speed: number;
  current_job: string | null;
  version: string;
  cpu_limit: number;
  ram_limit: number;
  priority: number;
  is_paused: boolean;
  last_seen: string;
  registered_at: string;
}

export interface JobCreate {
  title: string;
  description?: string;
  job_type: JobType;
  priority: JobPriority;
  payload: Record<string, unknown>;
  target_worker_id?: string;
  max_retries: number;
  timeout_seconds?: number;
}

export interface JobResponse {
  id: string;
  title: string;
  description: string | null;
  job_type: JobType;
  priority: JobPriority;
  status: JobStatus;
  progress: number;
  payload: Record<string, unknown>;
  result: unknown;
  error: string | null;
  worker_id: string | null;
  created_by: string | null;
  retry_count: number;
  max_retries: number;
  timeout_seconds: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  estimated_completion: string | null;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  context?: Record<string, unknown>;
  stream: boolean;
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  worker_id: string | null;
  tokens_used: number | null;
  execution_time_ms: number | null;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  role: UserRole;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface SystemMetrics {
  total_workers: number;
  online_workers: number;
  busy_workers: number;
  offline_workers: number;
  paused_workers: number;
  total_jobs: number;
  running_jobs: number;
  queued_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_cpu_percent: number;
  total_ram_used_gb: number;
  total_ram_available_gb: number;
  jobs_per_second: number;
  avg_execution_time_ms: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface WorkerSettingsUpdate {
  cpu_limit?: number;
  ram_limit_gb?: number;
  priority?: number;
  allowed_hours_start?: number;
  allowed_hours_end?: number;
  idle_only?: boolean;
  auto_pause?: boolean;
  auto_resume?: boolean;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: string;
  source: string;
  worker_id: string | null;
  message: string;
  details: unknown;
}
