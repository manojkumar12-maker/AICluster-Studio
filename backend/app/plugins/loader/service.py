import importlib
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

from ..manifest.service import PluginManifest

logger = logging.getLogger(__name__)


class PluginLoader:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)

    async def load_plugin(self, plugin_id: str, manifest: PluginManifest) -> bool:
        plugin_path = self.plugins_dir / plugin_id
        if not plugin_path.exists():
            logger.error(f"Plugin path not found: {plugin_path}")
            return False
        sys.path.insert(0, str(plugin_path))
        try:
            module = importlib.import_module(manifest.entry_point.replace(".py", ""))
            if hasattr(module, "Plugin"):
                plugin_class = getattr(module, "Plugin")
                instance = plugin_class()
                logger.info(f"Plugin loaded: {plugin_id} v{manifest.version}")
                return True
            else:
                logger.warning(f"Plugin {plugin_id} has no 'Plugin' class")
                return False
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}")
            return False

    async def unload_plugin(self, plugin_id: str):
        for key in list(sys.modules.keys()):
            if plugin_id in key:
                del sys.modules[key]

    async def discover_plugins(self) -> list[Path]:
        return [p for p in self.plugins_dir.iterdir() if p.is_dir() and (p / "plugin.json").exists()]
