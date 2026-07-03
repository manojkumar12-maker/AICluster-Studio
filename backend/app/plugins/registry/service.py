import logging
from datetime import datetime, timezone
from typing import Any

from ..manifest.service import PluginManifest

logger = logging.getLogger(__name__)


class PluginInfo:
    def __init__(self, manifest: PluginManifest, status: str = "registered",
                 loaded_at: datetime | None = None):
        self.manifest = manifest
        self.status = status
        self.loaded_at = loaded_at or datetime.now(timezone.utc)
        self.instance: Any = None
        self.hooks: dict[str, Any] = {}


class PluginRegistry:
    _plugins: dict[str, PluginInfo] = {}

    @classmethod
    def register(cls, manifest: PluginManifest) -> bool:
        if manifest.plugin_id in cls._plugins:
            logger.warning(f"Plugin already registered: {manifest.plugin_id}")
            return False
        cls._plugins[manifest.plugin_id] = PluginInfo(manifest=manifest)
        logger.info(f"Plugin registered: {manifest.plugin_id} v{manifest.version}")
        return True

    @classmethod
    def get(cls, plugin_id: str) -> PluginInfo | None:
        return cls._plugins.get(plugin_id)

    @classmethod
    def set_status(cls, plugin_id: str, status: str):
        info = cls._plugins.get(plugin_id)
        if info:
            info.status = status

    @classmethod
    def set_instance(cls, plugin_id: str, instance: Any):
        info = cls._plugins.get(plugin_id)
        if info:
            info.instance = instance

    @classmethod
    def remove(cls, plugin_id: str) -> bool:
        if plugin_id in cls._plugins:
            del cls._plugins[plugin_id]
            return True
        return False

    @classmethod
    def list_plugins(cls) -> list[dict]:
        return [{
            "id": p.manifest.plugin_id, "name": p.manifest.name,
            "version": p.manifest.version, "type": p.manifest.plugin_type,
            "status": p.status, "author": p.manifest.author,
            "hooks": p.manifest.hooks,
        } for p in cls._plugins.values()]

    @classmethod
    def find_by_hook(cls, hook: str) -> list[PluginInfo]:
        return [p for p in cls._plugins.values() if hook in p.manifest.hooks and p.status == "active"]
