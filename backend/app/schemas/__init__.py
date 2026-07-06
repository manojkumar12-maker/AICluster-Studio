from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class WorkerRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    hostname: str = Field(..., min_length=1, max_length=255)
    ip: str = Field(..., max_length=45)


class WorkerRegisterResponse(BaseModel):
    id: str


class HeartbeatRequest(BaseModel):
    id: str = Field(..., max_length=36)
    cpu: float = Field(..., ge=0, le=100)
    ram: float = Field(..., ge=0, le=100)
    disk: float = Field(..., ge=0, le=100)
    temperature: Optional[float] = None
    busy: bool = False
    network_speed: float = 0.0
    version: Optional[str] = None


class WorkerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    worker_name: str
    hostname: str
    ip: str
    status: str
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    temperature: Optional[float]
    network_speed: float
    current_job: Optional[str]
    version: str
    cpu_limit: float
    ram_limit: float
    priority: int
    is_paused: bool
    last_seen: datetime
    registered_at: datetime


class DashboardResponse(BaseModel):
    total_workers: int
    online_workers: int
    online: int
    offline: int
    idle: int
    busy: int
    average_cpu: float
    average_ram: float
    active_jobs: int
    queued_jobs: int
    queue_depth: int
    running_jobs: int
    repositories: int = 0
    plugins: int = 0
    workflows: int = 0


class JobCreateRequest(BaseModel):
    type: str = Field(default="custom", max_length=64)
    payload: dict = Field(default_factory=dict)
    priority: int = Field(default=2, ge=1, le=5)


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    status: str
    assigned_worker: Optional[str]
    progress: float
    priority: int
    error: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class HealthResponse(BaseModel):
    status: str
    database: str
    worker_count: int
    version: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    email: str = ""
    role: str
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SystemLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    level: str
    message: str
    source: Optional[str]
    created_at: datetime


class ProgressRequest(BaseModel):
    job_id: str
    progress: float = Field(..., ge=0, le=100)
    logs: Optional[str] = None


class ResultRequest(BaseModel):
    job_id: str
    status: str = Field(..., pattern="^(completed|failed|cancelled|timeout)$")
    result: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    logs: Optional[str] = None


class NextJobResponse(BaseModel):
    job: Optional[JobResponse] = None
