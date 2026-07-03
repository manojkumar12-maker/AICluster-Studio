from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from .models import WorkerStatus, JobStatus, JobPriority, JobType, UserRole


class HeartbeatData(BaseModel):
    worker_id: str
    hostname: str
    cpu_percent: float = Field(..., ge=0, le=100)
    ram_total: float = Field(..., ge=0)
    ram_used: float = Field(..., ge=0)
    disk_total: float = Field(..., ge=0)
    disk_used: float = Field(..., ge=0)
    temperature: Optional[float] = None
    network_rx: int = Field(default=0, ge=0)
    network_tx: int = Field(default=0, ge=0)
    status: WorkerStatus
    current_job: Optional[str] = None
    uptime: float = Field(default=0, ge=0)
    version: str


class WorkerRegister(BaseModel):
    hostname: str
    ip_address: str
    port: int = Field(default=8001, ge=1024, le=65535)
    version: str
    cpu_limit: float = Field(default=25, ge=1, le=100)
    ram_limit_gb: float = Field(default=8, ge=1, le=1024)


class WorkerResponse(BaseModel):
    id: str
    hostname: str
    ip_address: str
    port: int
    cpu_percent: float
    cpu_limit: float
    ram_total: float
    ram_used: float
    ram_limit: float
    disk_total: float
    disk_used: float
    temperature: Optional[float]
    status: WorkerStatus
    current_job: Optional[str]
    version: str
    last_heartbeat: datetime
    uptime: float
    is_paused: bool = False
    allowed_hours_start: Optional[int] = None
    allowed_hours_end: Optional[int] = None
    idle_only: bool = False
    priority: int = Field(default=0, ge=0)

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    title: str
    description: Optional[str] = None
    job_type: JobType = JobType.CUSTOM
    priority: JobPriority = JobPriority.MEDIUM
    payload: dict[str, Any] = Field(default_factory=dict)
    target_worker_id: Optional[str] = None
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(default=None, ge=10)


class JobResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    job_type: JobType
    priority: JobPriority
    status: JobStatus
    progress: float = Field(default=0, ge=0, le=100)
    payload: dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    worker_id: Optional[str] = None
    created_by: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[int]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[dict[str, Any]] = None
    stream: bool = True


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    worker_id: Optional[str] = None
    tokens_used: Optional[int] = None
    execution_time_ms: Optional[int] = None


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.DEVELOPER


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str


class SystemMetrics(BaseModel):
    total_workers: int
    online_workers: int
    busy_workers: int
    offline_workers: int
    paused_workers: int
    total_jobs: int
    running_jobs: int
    queued_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_cpu_percent: float
    total_ram_used_gb: float
    total_ram_available_gb: float
    jobs_per_second: float
    avg_execution_time_ms: float


class LogEntry(BaseModel):
    id: str
    timestamp: datetime
    level: str
    source: str
    worker_id: Optional[str] = None
    message: str
    details: Optional[Any] = None


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int


class SettingsUpdate(BaseModel):
    key: str
    value: Any


class WorkerSettingsUpdate(BaseModel):
    cpu_limit: Optional[float] = Field(default=None, ge=1, le=100)
    ram_limit_gb: Optional[float] = Field(default=None, ge=1, le=1024)
    priority: Optional[int] = Field(default=None, ge=0)
    allowed_hours_start: Optional[int] = Field(default=None, ge=0, le=23)
    allowed_hours_end: Optional[int] = Field(default=None, ge=0, le=23)
    idle_only: Optional[bool] = None
    auto_pause: Optional[bool] = None
    auto_resume: Optional[bool] = None
