import logging
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def schema(self) -> dict: ...

    @abstractmethod
    async def execute(self, input: dict, db: AsyncSession) -> dict: ...


class ToolRegistry:
    _tools: dict[str, type[BaseTool]] = {}

    @classmethod
    def register(cls, tool_class: type[BaseTool]):
        instance = tool_class()
        cls._tools[instance.name()] = tool_class
        logger.info(f"Tool registered: {instance.name()}")

    @classmethod
    def get_tool(cls, name: str) -> type[BaseTool] | None:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> list[str]:
        return list(cls._tools.keys())

    @classmethod
    def get_schemas(cls) -> list[dict]:
        schemas = []
        for name, tool_class in cls._tools.items():
            instance = tool_class()
            schemas.append({
                "name": instance.name(),
                "description": instance.description(),
                "schema": instance.schema(),
            })
        return schemas

    @classmethod
    async def execute_tool(cls, name: str, input: dict, db: AsyncSession) -> dict:
        tool_class = cls._tools.get(name)
        if not tool_class:
            return {"error": f"Tool '{name}' not found"}
        instance = tool_class()
        return await instance.execute(input, db)
