import json
import logging
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

logger = logging.getLogger(__name__)

PLUGIN_TYPES = [
    "workflow", "agent", "tool", "repository", "parser", "language",
    "llm_provider", "dashboard", "metrics", "worker", "scheduler",
    "notification", "auth", "storage", "visualization", "custom",
]

HOOK_TYPES = [
    "on_startup", "on_shutdown", "on_workflow_start", "on_workflow_finish",
    "on_task_start", "on_task_finish", "on_repository_scan", "on_repository_indexed",
    "on_agent_created", "on_llm_response", "on_tool_execution",
    "on_worker_connected", "on_worker_disconnected", "on_backup", "on_restore",
]


class PluginManifest(BaseModel):
    plugin_id: str = Field(..., pattern=r"^[a-z0-9_-]+$")
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    homepage: str = ""
    license: str = "MIT"
    plugin_type: str = "custom"
    min_platform_version: str = "1.0.0"
    max_platform_version: str = ""
    dependencies: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    hooks: list[str] = Field(default_factory=list)
    entry_point: str = "main.py"
    config: dict = Field(default_factory=dict)


class ManifestService:
    @staticmethod
    def validate(manifest: PluginManifest) -> list[str]:
        errors = []
        if manifest.plugin_type not in PLUGIN_TYPES:
            errors.append(f"Invalid plugin type: {manifest.plugin_type}. Must be one of {PLUGIN_TYPES}")
        for hook in manifest.hooks:
            if hook not in HOOK_TYPES:
                errors.append(f"Unknown hook: {hook}")
        if not manifest.entry_point:
            errors.append("entry_point is required")
        return errors

    @staticmethod
    def load(path: str | Path) -> PluginManifest | None:
        manifest_path = Path(path) / "plugin.json"
        if not manifest_path.exists():
            logger.error(f"Manifest not found: {manifest_path}")
            return None
        try:
            with open(manifest_path) as f:
                data = json.load(f)
            manifest = PluginManifest(**data)
            return manifest
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to load manifest: {e}")
            return None

    @staticmethod
    def check_compatibility(manifest: PluginManifest, platform_version: str = "1.1.0") -> tuple[bool, str]:
        min_v = [int(x) for x in manifest.min_platform_version.split(".")]
        plat_v = [int(x) for x in platform_version.split(".")]
        if plat_v < min_v:
            return False, f"Requires platform >= {manifest.min_platform_version}"
        if manifest.max_platform_version:
            max_v = [int(x) for x in manifest.max_platform_version.split(".")]
            if plat_v > max_v:
                return False, f"Requires platform <= {manifest.max_platform_version}"
        return True, "Compatible"
