from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class WorkerStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"
    SHUTDOWN = "shutdown"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class JobType(str, Enum):
    AI_CHAT = "ai_chat"
    CODE_ANALYSIS = "code_analysis"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    FILE_PROCESSING = "file_processing"
    CUSTOM = "custom"


class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


@dataclass
class WorkerInfo:
    id: str
    hostname: str
    ip_address: str
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
    network_rx: int
    network_tx: int
