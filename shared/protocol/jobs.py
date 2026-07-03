from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class JobAssignment(BaseModel):
    id: str
    type: str = "custom"
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 2


class NextJobResponse(BaseModel):
    job: JobAssignment | None = None


class ProgressRequest(BaseModel):
    job_id: str
    progress: float = Field(..., ge=0, le=100)
    logs: str | None = None


class ProgressResponse(BaseModel):
    status: str = "ok"


class ResultRequest(BaseModel):
    job_id: str
    status: str = Field(..., pattern="^(completed|failed|cancelled|timeout)$")
    result: dict[str, Any] | None = None
    error: str | None = None
    duration_ms: float | None = None
    logs: str | None = None


class ResultResponse(BaseModel):
    status: str = "ok"
