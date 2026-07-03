import logging
from typing import Any

logger = logging.getLogger(__name__)


class AuditEvent:
    def __init__(self, event_type: str, category: str = "system", severity: str = "INFO",
                 message: str | None = None, user_id: str | None = None,
                 username: str | None = None, worker_id: str | None = None,
                 workflow_id: str | None = None, repository_id: str | None = None,
                 plugin_id: str | None = None, agent_id: str | None = None,
                 session_id: str | None = None, resource_type: str | None = None,
                 resource_id: str | None = None, action: str | None = None,
                 status: str | None = None, duration_ms: float | None = None,
                 ip_address: str | None = None, extra: dict | None = None,
                 old_value: dict | None = None, new_value: dict | None = None,
                 request_id: str | None = None, trace_id: str | None = None,
                 **kwargs):
        self.event_type = event_type
        self.category = category
        self.severity = severity
        self.message = message
        self.user_id = user_id
        self.username = username
        self.worker_id = worker_id
        self.workflow_id = workflow_id
        self.repository_id = repository_id
        self.plugin_id = plugin_id
        self.agent_id = agent_id
        self.session_id = session_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.action = action
        self.status = status
        self.duration_ms = duration_ms
        self.ip_address = ip_address
        self.extra = extra or {}
        self.old_value = old_value or {}
        self.new_value = new_value or {}
        self.request_id = request_id
        self.trace_id = trace_id


class EventBus:
    _listeners: list[callable] = []

    @classmethod
    def subscribe(cls, listener: callable):
        cls._listeners.append(listener)

    @classmethod
    async def publish(cls, event: AuditEvent):
        for listener in cls._listeners:
            try:
                await listener(event)
            except Exception as e:
                logger.error(f"Audit listener error: {e}")

    @classmethod
    def unsubscribe(cls, listener: callable):
        cls._listeners = [l for l in cls._listeners if l is not listener]
