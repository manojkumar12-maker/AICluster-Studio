import asyncio
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import psutil
from fastapi import APIRouter, HTTPException

from ..schemas import (
    StatusResponse, ConfigResponse, ConfigUpdateRequest,
    ConnectionTestResult, SystemInfoResponse, LogEntry,
    InstallStep, ActionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

CC_DIR = Path(__file__).resolve().parent.parent.parent.parent
WORKER_DIR = CC_DIR.parent / "worker"
WORKER_CONFIG_FILE = WORKER_DIR / "config.json"
WORKER_VENV = WORKER_DIR / ".venv"
WORKER_MAIN = WORKER_DIR / "scripts" / "run.py"
WORKER_LOG_FILE = WORKER_DIR / "logs" / "worker.log"

worker_process: Optional[asyncio.subprocess.Process] = None
worker_id_store: Optional[str] = None
worker_start_time: Optional[float] = None
jobs_completed = 0
jobs_failed = 0


def _load_worker_config() -> dict:
    try:
        if WORKER_CONFIG_FILE.exists():
            with open(WORKER_CONFIG_FILE) as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_worker_config(config: dict):
    WORKER_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WORKER_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def _get_worker_status() -> str:
    global worker_process
    if worker_process is None:
        return "stopped"
    if worker_process.returncode is not None:
        return "stopped"
    return "running"


@router.get("/status", response_model=StatusResponse)
async def get_status():
    global worker_process, worker_id_store, worker_start_time, jobs_completed, jobs_failed
    config = _load_worker_config()
    status = _get_worker_status()
    cpu = psutil.cpu_percent(interval=0.3) if status == "running" else 0.0
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime = (time.time() - worker_start_time) if worker_start_time and status == "running" else 0.0

    heartbeat = "unknown"
    last_hb = None
    if worker_id_store:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{config.get('master_url', 'http://localhost:8000')}/api/v1/workers/{worker_id_store}")
                if resp.status_code == 200:
                    w = resp.json()
                    heartbeat = "ok" if w.get("status") in ("online", "busy") else "offline"
                    last_hb = w.get("last_seen")
        except Exception:
            heartbeat = "unreachable"

    return StatusResponse(
        worker_id=worker_id_store,
        worker_name=config.get("worker_name", ""),
        status=status,
        master_url=config.get("master_url", ""),
        cpu_percent=round(cpu, 1),
        ram_percent=round(mem.percent, 1),
        disk_percent=round(disk.percent, 1),
        uptime_seconds=round(uptime, 1),
        jobs_completed=jobs_completed,
        jobs_failed=jobs_failed,
        heartbeat_status=heartbeat,
        last_heartbeat=last_hb,
        is_paused=False,
        connection_quality="good" if heartbeat == "ok" else "poor",
    )


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    config = _load_worker_config()
    return ConfigResponse(
        master_url=config.get("master_url", "http://localhost:8000"),
        worker_name=config.get("worker_name", ""),
        heartbeat_interval=config.get("heartbeat_interval", 5),
        poll_interval=config.get("poll_interval", 5),
        log_level=config.get("log_level", "INFO"),
        version=config.get("version", "1.0.0"),
        worker_description=config.get("worker_description", ""),
        auto_start=config.get("auto_start", False),
        launch_with_windows=config.get("launch_with_windows", False),
        auto_reconnect=config.get("auto_reconnect", True),
    )


@router.post("/config", response_model=ActionResponse)
async def update_config(data: ConfigUpdateRequest):
    config = _load_worker_config()
    updates = data.model_dump(exclude_none=True)
    config.update(updates)
    _save_worker_config(config)
    return ActionResponse(success=True, message="Configuration saved")


@router.post("/config/reset", response_model=ActionResponse)
async def reset_config():
    default_config = {
        "master_url": "http://localhost:8000",
        "worker_name": "",
        "heartbeat_interval": 5,
        "poll_interval": 5,
        "log_level": "INFO",
        "version": "1.0.0",
        "worker_description": "",
        "auto_start": False,
        "launch_with_windows": False,
        "auto_reconnect": True,
    }
    _save_worker_config(default_config)
    return ActionResponse(success=True, message="Configuration reset to defaults")


@router.post("/start", response_model=ActionResponse)
async def start_worker():
    global worker_process, worker_start_time

    if _get_worker_status() == "running":
        return ActionResponse(success=True, message="Worker is already running")

    if not WORKER_MAIN.exists():
        return ActionResponse(success=False, message=f"Worker entry point not found: {WORKER_MAIN}")

    venv_python = WORKER_VENV / "Scripts" / "python.exe"
    python_path = str(venv_python) if venv_python.exists() else sys.executable

    try:
        worker_process = await asyncio.create_subprocess_exec(
            python_path, str(WORKER_MAIN),
            cwd=str(WORKER_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        worker_start_time = time.time()
        logger.info(f"Worker started (PID: {worker_process.pid})")
        return ActionResponse(success=True, message=f"Worker started (PID: {worker_process.pid})")
    except Exception as e:
        return ActionResponse(success=False, message=f"Failed to start worker: {e}")


@router.post("/stop", response_model=ActionResponse)
async def stop_worker():
    global worker_process, worker_start_time

    if worker_process is None:
        return ActionResponse(success=True, message="Worker is not running")

    try:
        worker_process.terminate()
        try:
            await asyncio.wait_for(worker_process.wait(), timeout=5)
        except asyncio.TimeoutError:
            worker_process.kill()
            await worker_process.wait()
        worker_process = None
        worker_start_time = None
        logger.info("Worker stopped")
        return ActionResponse(success=True, message="Worker stopped")
    except Exception as e:
        return ActionResponse(success=False, message=f"Failed to stop worker: {e}")


@router.post("/restart", response_model=ActionResponse)
async def restart_worker():
    await stop_worker()
    await asyncio.sleep(1)
    return await start_worker()


@router.post("/register", response_model=ActionResponse)
async def register_worker():
    global worker_id_store
    config = _load_worker_config()
    master_url = config.get("master_url", "http://localhost:8000")
    worker_name = config.get("worker_name", "") or socket.gethostname()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{master_url}/api/v1/workers/register",
                json={"name": worker_name, "hostname": worker_name, "ip": "127.0.0.1"},
            )
            if resp.status_code == 200:
                data = resp.json()
                worker_id_store = data.get("id")
                logger.info(f"Registered with master: {worker_id_store}")
                return ActionResponse(success=True, message=f"Registered: {worker_id_store}")
            else:
                return ActionResponse(success=False, message=f"Registration failed: {resp.status_code}")
    except Exception as e:
        return ActionResponse(success=False, message=f"Registration error: {e}")


@router.post("/test-connection", response_model=ConnectionTestResult)
async def test_connection(data: Optional[dict] = None):
    config = _load_worker_config()
    master_url = (data or {}).get("master_url") or config.get("master_url", "http://localhost:8000")
    result = ConnectionTestResult()
    latencies = []

    for i in range(3):
        try:
            start = time.time()
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"{master_url}/api/v1/health")
                elapsed = (time.time() - start) * 1000
                if resp.status_code == 200:
                    latencies.append(elapsed)
                    result.ping = "pass"
                    result.master_version = resp.json().get("version", "unknown")
                else:
                    result.ping = "fail"
        except Exception:
            result.ping = "fail"

    if latencies:
        result.average_latency_ms = round(sum(latencies) / len(latencies), 1)
        result.packet_loss_percent = round((1 - len(latencies) / 3) * 100, 1)

    if result.ping == "pass":
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{master_url}/api/v1/health")
                result.rest_api = "pass" if resp.status_code == 200 else "fail"
        except Exception:
            result.rest_api = "fail"

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    f"{master_url}/api/v1/auth/login",
                    json={"username": "admin", "password": "admin123"},
                )
                result.auth = "pass" if resp.status_code == 200 else "fail"
        except Exception:
            result.auth = "fail"

        try:
            worker_name = config.get("worker_name", "") or socket.gethostname()
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    f"{master_url}/api/v1/workers/register",
                    json={"name": worker_name, "hostname": worker_name, "ip": "127.0.0.1"},
                )
                if resp.status_code == 200:
                    result.worker_registration = "pass"
                    result.worker_id = resp.json().get("id")
                else:
                    result.worker_registration = "fail"
        except Exception:
            result.worker_registration = "fail"

    result.details = f"Master: {master_url}, Latency: {result.average_latency_ms}ms"
    return result


@router.get("/logs", response_model=list[LogEntry])
async def get_logs(limit: int = 100):
    entries = []
    if not WORKER_LOG_FILE.exists():
        return entries
    try:
        with open(WORKER_LOG_FILE, encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                entries.append(LogEntry(
                    timestamp=parts[0],
                    level=parts[1].strip("[]"),
                    message=parts[2],
                    source="worker",
                ))
    except (OSError, UnicodeDecodeError):
        pass
    return entries


@router.post("/logs/export", response_model=ActionResponse)
async def export_logs():
    if not WORKER_LOG_FILE.exists():
        return ActionResponse(success=False, message="No log file found")
    export_path = WORKER_DIR / "logs" / f"worker-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    try:
        shutil.copy2(WORKER_LOG_FILE, export_path)
        return ActionResponse(success=True, message=f"Logs exported to {export_path}")
    except Exception as e:
        return ActionResponse(success=False, message=f"Export failed: {e}")


@router.post("/logs/clear", response_model=ActionResponse)
async def clear_logs():
    try:
        if WORKER_LOG_FILE.exists():
            open(WORKER_LOG_FILE, "w").close()
        return ActionResponse(success=True, message="Logs cleared")
    except Exception as e:
        return ActionResponse(success=False, message=f"Failed to clear logs: {e}")


@router.get("/system-info", response_model=SystemInfoResponse)
async def get_system_info():
    disk = psutil.disk_usage("/")
    mem = psutil.virtual_memory()
    git_available = shutil.which("git") is not None
    is_admin = False
    try:
        is_admin = os.name == "nt" and (os.system("net session >nul 2>&1") == 0)
    except Exception:
        pass

    master_online = False
    config = _load_worker_config()
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{config.get('master_url', 'http://localhost:8000')}/api/v1/health")
            master_online = resp.status_code == 200
    except Exception:
        pass

    return SystemInfoResponse(
        os=platform.system(),
        os_version=platform.version(),
        python_version=sys.version,
        python_path=sys.executable,
        git_installed=git_available,
        disk_free_gb=round(disk.free / (1024**3), 1),
        disk_total_gb=round(disk.total / (1024**3), 1),
        ram_total_gb=round(mem.total / (1024**3), 1),
        ram_free_gb=round(mem.available / (1024**3), 1),
        cpu_count=psutil.cpu_count(),
        cpu_percent=round(psutil.cpu_percent(interval=0.5), 1),
        is_admin=is_admin,
        worker_folder_exists=WORKER_DIR.exists(),
        log_folder_exists=(WORKER_DIR / "logs").exists(),
        has_permissions=os.access(str(WORKER_DIR), os.R_OK | os.W_OK),
        master_online=master_online,
    )


@router.get("/install/steps", response_model=list[InstallStep])
async def get_install_steps():
    steps = [
        InstallStep(step="System Requirements", status="pending"),
        InstallStep(step="Install Dependencies", status="pending"),
        InstallStep(step="Configure Worker", status="pending"),
        InstallStep(step="Test Connection", status="pending"),
        InstallStep(step="Register Worker", status="pending"),
        InstallStep(step="Start Worker", status="pending"),
    ]

    if WORKER_VENV.exists() and (WORKER_VENV / "Scripts" / "python.exe").exists():
        steps[0].status = "completed"
        steps[0].message = "Python virtual environment exists"

    if WORKER_CONFIG_FILE.exists():
        steps[2].status = "completed"
        steps[2].message = "Worker configuration exists"

    status = _get_worker_status()
    if status == "running":
        steps[-1].status = "completed"
        steps[-1].message = f"Worker is running (PID: {worker_process.pid if worker_process else 'unknown'})"

    return steps


@router.post("/install/run", response_model=ActionResponse)
async def run_installation():
    try:
        WORKER_DIR.mkdir(parents=True, exist_ok=True)
        (WORKER_DIR / "logs").mkdir(exist_ok=True)

        if not WORKER_VENV.exists():
            logger.info("Creating virtual environment...")
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "venv", str(WORKER_VENV),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode != 0:
                return ActionResponse(success=False, message="Failed to create virtual environment")

        venv_pip = WORKER_VENV / "Scripts" / "pip.exe"
        req_file = WORKER_DIR / "requirements.txt"
        if req_file.exists() and venv_pip.exists():
            logger.info("Installing dependencies...")
            proc = await asyncio.create_subprocess_exec(
                str(venv_pip), "install", "-r", str(req_file),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()

        if not WORKER_CONFIG_FILE.exists():
            _save_worker_config({
                "master_url": "http://localhost:8000",
                "worker_name": "",
                "heartbeat_interval": 5,
                "poll_interval": 5,
                "log_level": "INFO",
                "version": "1.0.0",
            })

        return ActionResponse(success=True, message="Installation complete")
    except Exception as e:
        return ActionResponse(success=False, message=f"Installation failed: {e}")


@router.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
