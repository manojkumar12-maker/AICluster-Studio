from pydantic import BaseModel, Field
from typing import Optional, Any


class StatusResponse(BaseModel):
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    status: str = "stopped"
    version: str = "1.0.0"
    master_url: Optional[str] = None
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    disk_percent: float = 0.0
    uptime_seconds: float = 0.0
    jobs_completed: int = 0
    jobs_failed: int = 0
    current_job: Optional[str] = None
    heartbeat_status: str = "unknown"
    last_heartbeat: Optional[str] = None
    is_paused: bool = False
    connection_quality: str = "unknown"


class ConfigResponse(BaseModel):
    master_url: str = "http://localhost:8000"
    worker_name: str = ""
    heartbeat_interval: int = 5
    poll_interval: int = 5
    log_level: str = "INFO"
    version: str = "1.0.0"
    worker_description: str = ""
    auto_start: bool = False
    launch_with_windows: bool = False
    auto_reconnect: bool = True


class ConfigUpdateRequest(BaseModel):
    master_url: Optional[str] = None
    worker_name: Optional[str] = None
    heartbeat_interval: Optional[int] = None
    poll_interval: Optional[int] = None
    log_level: Optional[str] = None
    version: Optional[str] = None
    worker_description: Optional[str] = None
    auto_start: Optional[bool] = None
    launch_with_windows: Optional[bool] = None
    auto_reconnect: Optional[bool] = None


class ConnectionTestResult(BaseModel):
    ping: str = "pending"
    rest_api: str = "pending"
    websocket: str = "pending"
    auth: str = "pending"
    worker_registration: str = "pending"
    average_latency_ms: float = 0.0
    packet_loss_percent: float = 0.0
    master_version: Optional[str] = None
    worker_id: Optional[str] = None
    details: str = ""


class SystemInfoResponse(BaseModel):
    os: str = ""
    os_version: str = ""
    python_version: str = ""
    python_path: str = ""
    git_installed: bool = False
    disk_free_gb: float = 0.0
    disk_total_gb: float = 0.0
    ram_total_gb: float = 0.0
    ram_free_gb: float = 0.0
    cpu_count: int = 0
    cpu_percent: float = 0.0
    is_admin: bool = False
    firewall_active: bool = False
    port_8000_reachable: bool = False
    master_online: bool = False
    worker_folder_exists: bool = False
    log_folder_exists: bool = False
    has_permissions: bool = False


class LogEntry(BaseModel):
    timestamp: str = ""
    level: str = "INFO"
    message: str = ""
    source: str = ""


class InstallStep(BaseModel):
    step: str = ""
    status: str = "pending"
    message: str = ""


class ActionResponse(BaseModel):
    success: bool = True
    message: str = ""
