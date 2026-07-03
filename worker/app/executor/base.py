import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseJobHandler(ABC):
    @abstractmethod
    async def execute(self, job_id: str, payload: dict) -> dict:
        ...
