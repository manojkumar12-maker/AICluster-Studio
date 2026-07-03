import logging

from .base import BaseJobHandler

logger = logging.getLogger(__name__)


class JobRegistry:
    def __init__(self):
        self._handlers: dict[str, BaseJobHandler] = {}

    def register(self, job_type: str, handler: BaseJobHandler):
        self._handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    def get_handler(self, job_type: str) -> BaseJobHandler | None:
        return self._handlers.get(job_type)

    @property
    def registered_types(self) -> list[str]:
        return list(self._handlers.keys())
