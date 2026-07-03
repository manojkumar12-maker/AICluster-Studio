from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    timestamp: datetime
    event_type: str
    category: str
    severity: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    worker_id: Optional[str] = None
    workflow_id: Optional[str] = None
    repository_id: Optional[str] = None
    plugin_id: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    duration_ms: Optional[float] = None
    message: Optional[str] = None
    request_id: Optional[str] = None


class AuditSearchRequest(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    event_type: Optional[str] = None
    username: Optional[str] = None
    worker_id: Optional[str] = None
    workflow_id: Optional[str] = None
    repository_id: Optional[str] = None
    plugin_id: Optional[str] = None
    status: Optional[str] = None
    text: Optional[str] = None
    limit: int = 100
    offset: int = 0


class AuditStatistics(BaseModel):
    total_events: int = 0
    today: int = 0
    this_week: int = 0
    critical: int = 0
    errors: int = 0
    warnings: int = 0
    success_rate: float = 0.0
    by_category: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    top_users: list[dict] = []
    top_workers: list[dict] = []
    top_plugins: list[dict] = []


class AuditSettingsResponse(BaseModel):
    retention_days: int = 90
    auto_purge_enabled: bool = True
    export_format: str = "csv"
    max_log_size_mb: int = 1000
    notification_on_critical: bool = True


class AuditSettingsUpdate(BaseModel):
    retention_days: Optional[int] = None
    auto_purge_enabled: Optional[bool] = None
    export_format: Optional[str] = None
    max_log_size_mb: Optional[int] = None
    notification_on_critical: Optional[bool] = None
