import logging
from typing import AsyncIterator

from ..providers.interface import ModelProvider

logger = logging.getLogger(__name__)


class ModelRegistry:
    _providers: dict[str, type[ModelProvider]] = {}
    _instances: dict[str, ModelProvider] = {}

    @classmethod
    def register_provider(cls, name: str, provider_class: type[ModelProvider]):
        cls._providers[name] = provider_class
        logger.info(f"Registered provider: {name}")

    @classmethod
    def get_provider(cls, name: str) -> type[ModelProvider] | None:
        return cls._providers.get(name)

    @classmethod
    def get_instance(cls, name: str) -> ModelProvider | None:
        return cls._instances.get(name)

    @classmethod
    def set_instance(cls, name: str, instance: ModelProvider):
        cls._instances[name] = instance

    @classmethod
    def remove_instance(cls, name: str):
        cls._instances.pop(name, None)

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def list_instances(cls) -> list[str]:
        return list(cls._instances.keys())

    @classmethod
    def list_capabilities(cls) -> dict[str, dict]:
        return {n: inst.capabilities() for n, inst in cls._instances.items()}
