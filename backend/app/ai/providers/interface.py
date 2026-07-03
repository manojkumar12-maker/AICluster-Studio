from abc import ABC, abstractmethod
from typing import AsyncIterator


class ModelProvider(ABC):
    @abstractmethod
    async def load(self) -> bool:
        ...

    @abstractmethod
    async def unload(self) -> bool:
        ...

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str | None = None,
                       max_tokens: int = 2048, temperature: float = 0.7) -> str:
        ...

    @abstractmethod
    async def stream(self, prompt: str, system_prompt: str | None = None,
                     max_tokens: int = 2048, temperature: float = 0.7) -> AsyncIterator[str]:
        ...

    @abstractmethod
    async def token_count(self, text: str) -> int:
        ...

    @abstractmethod
    async def health(self) -> bool:
        ...

    @abstractmethod
    def configuration(self) -> dict:
        ...

    @abstractmethod
    def capabilities(self) -> dict:
        ...
