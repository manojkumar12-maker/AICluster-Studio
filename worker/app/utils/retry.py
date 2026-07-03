import asyncio
import logging

from ..core.constants import RETRY_DELAYS

logger = logging.getLogger(__name__)


class RetryHandler:
    def __init__(self, delays: list[int] | None = None):
        self.delays = delays or RETRY_DELAYS
        self._attempt = 0

    @property
    def current_delay(self) -> int:
        idx = min(self._attempt, len(self.delays) - 1)
        return self.delays[idx]

    async def wait(self):
        delay = self.current_delay
        logger.info(f"Retry attempt {self._attempt + 1}, waiting {delay}s")
        await asyncio.sleep(delay)
        self._attempt += 1

    def reset(self):
        self._attempt = 0

    @property
    def attempt(self) -> int:
        return self._attempt
