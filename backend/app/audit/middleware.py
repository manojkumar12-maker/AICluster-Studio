import time
import uuid
import logging
from fastapi import Request, Response

from .events import EventBus, AuditEvent
from .service import AuditService
from ..database import get_db

logger = logging.getLogger(__name__)

SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "set-cookie"}
SENSITIVE_PATHS = {"/login", "/auth/login", "/token"}
SENSITIVE_BODIES = {"password", "token", "secret", "api_key", "access_token"}


class AuditMiddleware:
    def __init__(self):
        self.event_bus = EventBus()

    async def __call__(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
        start_time = time.time()

        response: Response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        if request.url.path.startswith("/api/v1/audit"):
            return response

        safe_headers = {k: v for k, v in request.headers.items() if k.lower() not in SENSITIVE_HEADERS}
        path = request.url.path

        event_data = {
            "request_id": request_id,
            "trace_id": trace_id,
            "ip_address": request.client.host if request.client else None,
            "duration_ms": round(duration_ms, 1),
            "extra": {
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "headers": safe_headers,
            },
        }

        is_sensitive = any(sp in path.lower() for sp in SENSITIVE_PATHS)

        if response.status_code >= 500:
            event_data["severity"] = "ERROR"
            event_data["event_type"] = "ERROR"
            event_data["message"] = f"HTTP {response.status_code} on {request.method} {path}"
        elif response.status_code >= 400:
            event_data["severity"] = "WARNING"
            event_data["event_type"] = "WARNING"
            event_data["message"] = f"HTTP {response.status_code} on {request.method} {path}"
        else:
            event_data["severity"] = "INFO"
            event_data["event_type"] = "SYSTEM_STARTED" if "health" in path else "CUSTOM_EVENT"
            event_data["message"] = f"{request.method} {path} -> {response.status_code}"

        if not is_sensitive:
            event = AuditEvent(**event_data, category="system")
            await self.event_bus.publish(event)

        return response
