import logging
import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...plugins.manifest.service import ManifestService, PluginManifest
from ...plugins.registry.service import PluginRegistry
from ...plugins.loader.service import PluginLoader
from ...plugins.hooks.service import HookRegistry
from ...websocket.manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plugins", tags=["plugins"])

PLUGINS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "plugins"
loader = PluginLoader(str(PLUGINS_DIR))


@router.get("")
async def list_plugins():
    return {"plugins": PluginRegistry.list_plugins(), "total": len(PluginRegistry._plugins)}


@router.post("/install")
async def install_plugin(data: dict):
    plugin_id = data.get("plugin_id", "")
    if not plugin_id:
        raise HTTPException(400, "plugin_id required")
    manifest = ManifestService.load(str(PLUGINS_DIR / plugin_id))
    if not manifest:
        raise HTTPException(404, f"Plugin manifest not found for {plugin_id}")
    errors = ManifestService.validate(manifest)
    if errors:
        raise HTTPException(400, f"Plugin validation failed: {errors}")
    ok, msg = ManifestService.check_compatibility(manifest)
    if not ok:
        raise HTTPException(400, f"Plugin incompatible: {msg}")
    if PluginRegistry.register(manifest):
        loaded = await loader.load_plugin(plugin_id, manifest)
        if loaded:
            PluginRegistry.set_status(plugin_id, "active")
            await ws_manager.broadcast("plugin_installed", {"id": plugin_id, "name": manifest.name})
            return {"status": "installed", "plugin_id": plugin_id, "manifest": manifest.model_dump()}
        else:
            PluginRegistry.set_status(plugin_id, "load_failed")
            return {"status": "load_failed", "plugin_id": plugin_id}
    return {"status": "already_registered", "plugin_id": plugin_id}


@router.post("/install/upload")
async def upload_plugin(file: UploadFile = File(...)):
    plugin_dir = PLUGINS_DIR / file.filename.replace(".zip", "")
    plugin_dir.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    import zipfile
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(content)) as zf:
        zf.extractall(str(plugin_dir))
    manifest = ManifestService.load(str(plugin_dir))
    if not manifest:
        raise HTTPException(400, "No valid plugin.json found in archive")
    PluginRegistry.register(manifest)
    return {"status": "uploaded", "plugin_id": manifest.plugin_id, "name": manifest.name}


@router.post("/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    info = PluginRegistry.get(plugin_id)
    if not info:
        raise HTTPException(404, "Plugin not found")
    PluginRegistry.set_status(plugin_id, "active")
    await ws_manager.broadcast("plugin_enabled", {"id": plugin_id})
    return {"status": "enabled"}


@router.post("/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    info = PluginRegistry.get(plugin_id)
    if not info:
        raise HTTPException(404, "Plugin not found")
    PluginRegistry.set_status(plugin_id, "disabled")
    await ws_manager.broadcast("plugin_disabled", {"id": plugin_id})
    return {"status": "disabled"}


@router.post("/{plugin_id}/uninstall")
async def uninstall_plugin(plugin_id: str):
    info = PluginRegistry.get(plugin_id)
    if not info:
        raise HTTPException(404, "Plugin not found")
    await loader.unload_plugin(plugin_id)
    PluginRegistry.remove(plugin_id)
    await ws_manager.broadcast("plugin_uninstalled", {"id": plugin_id})
    return {"status": "uninstalled"}


@router.get("/hooks")
async def list_hooks():
    return {"hooks": HookRegistry.list_hooks(), "available": [
        "on_startup", "on_shutdown", "on_workflow_start", "on_workflow_finish",
        "on_task_start", "on_task_finish", "on_repository_scan", "on_repository_indexed",
        "on_agent_created", "on_llm_response", "on_tool_execution",
        "on_worker_connected", "on_worker_disconnected", "on_backup", "on_restore",
    ]}


@router.post("/hooks/{hook}/trigger")
async def trigger_hook(hook: str, data: dict = {}):
    results = await HookRegistry.trigger(hook, **data)
    return {"hook": hook, "results": results}
