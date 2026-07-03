import asyncio
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class HookRegistry:
    _hooks: dict[str, list[tuple[str, int, Callable]]] = {}

    @classmethod
    def register(cls, hook: str, plugin_id: str, callback: Callable, priority: int = 0):
        if hook not in cls._hooks:
            cls._hooks[hook] = []
        cls._hooks[hook].append((plugin_id, priority, callback))
        cls._hooks[hook].sort(key=lambda x: x[1])
        logger.info(f"Hook registered: {hook} by {plugin_id}")

    @classmethod
    async def trigger(cls, hook: str, **kwargs) -> list[Any]:
        results = []
        callbacks = cls._hooks.get(hook, [])
        for plugin_id, priority, callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    result = await callback(**kwargs)
                else:
                    result = callback(**kwargs)
                results.append({"plugin_id": plugin_id, "result": result})
            except Exception as e:
                logger.error(f"Hook {hook} failed for {plugin_id}: {e}")
                results.append({"plugin_id": plugin_id, "error": str(e)})
        return results

    @classmethod
    def list_hooks(cls) -> dict[str, list[str]]:
        return {hook: [p[0] for p in callbacks] for hook, callbacks in cls._hooks.items()}
