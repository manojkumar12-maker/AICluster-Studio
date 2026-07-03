from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    detail: str
    retry_after: Optional[int] = None
