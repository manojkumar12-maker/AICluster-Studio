import logging
from typing import AsyncIterator

from ..registry.service import ModelRegistry
from ..providers.interface import ModelProvider

logger = logging.getLogger(__name__)

TASK_ROUTING = {
    "code_generation": {"provider": "ollama", "model": "qwen3-coder", "priority": 1},
    "architecture_review": {"provider": "openai-compatible", "model": "deepseek-coder", "priority": 2},
    "documentation": {"provider": "ollama", "model": "gemma3", "priority": 3},
    "summarization": {"provider": "llama.cpp", "model": "phi-3", "priority": 4},
    "default": {"provider": "ollama", "model": "qwen3-coder", "priority": 5},
}

PROFILES = {
    "fast": {"max_tokens": 1024, "temperature": 0.3},
    "balanced": {"max_tokens": 4096, "temperature": 0.5},
    "maximum_quality": {"max_tokens": 8192, "temperature": 0.7},
    "offline_low_ram": {"max_tokens": 512, "temperature": 0.3},
    "custom": {"max_tokens": 4096, "temperature": 0.5},
}


class ModelRouter:
    def __init__(self, registry: type[ModelRegistry]):
        self.registry = registry

    def select_provider(self, task_type: str = "default", profile: str = "balanced") -> tuple[ModelProvider | None, dict]:
        route = TASK_ROUTING.get(task_type, TASK_ROUTING["default"])
        profile_config = PROFILES.get(profile, PROFILES["balanced"])

        provider_name = route["provider"]
        instance = self.registry.get_instance(provider_name)
        if instance:
            logger.info(f"Router selected: {provider_name} for {task_type}")
            return instance, profile_config

        provider_class = self.registry.get_provider(provider_name)
        if provider_class:
            instance = provider_class(model=route["model"])
            self.registry.set_instance(provider_name, instance)
            return instance, profile_config

        for pname in self.registry.list_instances():
            instance = self.registry.get_instance(pname)
            if instance:
                return instance, profile_config

        logger.warning(f"No provider available for {task_type}")
        return None, profile_config

    async def generate(self, prompt: str, system_prompt: str | None = None,
                       task_type: str = "default", profile: str = "balanced") -> str:
        provider, config = self.select_provider(task_type, profile)
        if not provider:
            return "No model provider available. Install Ollama, llama.cpp, or an OpenAI-compatible server."
        return await provider.generate(prompt, system_prompt, config["max_tokens"], config["temperature"])

    async def stream(self, prompt: str, system_prompt: str | None = None,
                     task_type: str = "default", profile: str = "balanced") -> AsyncIterator[str]:
        provider, config = self.select_provider(task_type, profile)
        if not provider:
            yield "No model provider available."
            return
        async for token in provider.stream(prompt, system_prompt, config["max_tokens"], config["temperature"]):
            yield token

    def list_providers(self) -> list[dict]:
        providers = []
        for name in self.registry.list_instances():
            inst = self.registry.get_instance(name)
            if inst:
                providers.append({"name": name, "capabilities": inst.capabilities(), "config": inst.configuration()})
        for name in self.registry.list_providers():
            if name not in [p["name"] for p in providers]:
                providers.append({"name": name, "capabilities": {}, "config": {"type": name}})
        return providers
