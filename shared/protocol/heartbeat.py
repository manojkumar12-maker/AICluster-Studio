from pydantic import BaseModel, Field
from typing import Optional


class HeartbeatRequest(BaseModel):
    id: str = Field(..., max_length=36)
    cpu: float = Field(..., ge=0, le=100)
    ram: float = Field(..., ge=0, le=100)
    disk: float = Field(..., ge=0, le=100)
    temperature: Optional[float] = None
    busy: bool = False
    network_speed: float = 0.0
    version: str = "1.0.0"


class HeartbeatResponse(BaseModel):
    status: str
