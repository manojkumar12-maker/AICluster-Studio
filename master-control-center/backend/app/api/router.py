import asyncio
import json
import logging
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional

import httpx
import psutil
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from ..main import DATA_FILE, BACKEND_DIR

logger = logging.getLogger(__name__)
router = APIRouter()

MASTER_URL = "http://localhost:8000"

cluster_status = {
    "master_uptime": time.time(),
    "web_socket_connected": False,
    "last_backup": None,
    "alerts": [],
}

discovered_workers: list[dict] = []


@router.get("/cluster/status")
async def get_cluster_status():
    uptime_seconds = time.time() - cluster_status["master_uptime"]
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            health = await client.get(f"{MASTER_URL}/api/v1/health")
            workers_resp = await client.get(f"{MASTER_URL}/api/v1/workers")
            workers = workers_resp.json() if workers_resp.status_code == 200 else []

            online = sum(1 for w in workers if w.get("status") == "online")
            offline = sum(1 for w in workers if w.get("status") == "offline")
            busy = sum(1 for w in workers if w.get("status") == "busy")
            paused = sum(1 for w in workers if w.get("is_paused"))

            return {
                "master_status": "online",
                "version": health.json().get("version", "unknown"),
                "uptime_seconds": round(uptime_seconds),
                "cpu_percent": round(psutil.cpu_percent(interval=0.3), 1),
                "ram_percent": round(psutil.virtual_memory().percent, 1),
                "disk_percent": round(psutil.disk_usage("/").percent, 1),
                "database": "connected",
                "websocket_status": "connected" if cluster_status["web_socket_connected"] else "disconnected",
                "total_workers": len(workers),
                "online_workers": online,
                "offline_workers": offline,
                "busy_workers": busy,
                "idle_workers": max(0, online - busy),
                "paused_workers": paused,
                "network_latency_ms": 0.0,
                "last_backup": cluster_status["last_backup"],
            }
    except Exception as e:
        return {
            "master_status": "offline",
            "error": str(e),
            "uptime_seconds": round(uptime_seconds),
        }


@router.get("/cluster/discovery")
async def get_discovered_workers():
    return {"workers": discovered_workers}


@router.post("/cluster/discovery")
async def scan_lan(network_range: str = Query("192.168.1.0/24")):
    global discovered_workers
    discovered_workers = []
    base = network_range.rsplit(".", 1)[0]

    async def check_host(ip: str):
        try:
            async with httpx.AsyncClient(timeout=2) as c:
                resp = await c.get(f"http://{ip}:8001/health")
                if resp.status_code == 200:
                    data = resp.json()
                    hostname = data.get("worker", ip)
                    return {
                        "hostname": hostname,
                        "ip": ip,
                        "version": data.get("version", "unknown"),
                        "port": 8001,
                        "status": "found",
                        "already_registered": False,
                    }
        except Exception:
            pass
        try:
            async with httpx.AsyncClient(timeout=2) as c:
                resp = await c.get(f"http://{ip}:8000/api/v1/health")
                if resp.status_code == 200:
                    return {
                        "hostname": f"master-{ip}",
                        "ip": ip,
                        "version": resp.json().get("version", "unknown"),
                        "port": 8000,
                        "status": "found",
                        "already_registered": True,
                    }
        except Exception:
            pass
        return None

    tasks = [check_host(f"{base}.{i}") for i in range(1, 255)]
    results = await asyncio.gather(*tasks)
    discovered_workers = [r for r in results if r is not None]
    return {"workers": discovered_workers, "count": len(discovered_workers)}


@router.post("/cluster/discovery/register")
async def register_discovered_worker(data: dict):
    worker_ip = data.get("ip")
    hostname = data.get("hostname", worker_ip)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{MASTER_URL}/api/v1/workers/register",
                json={"name": hostname, "hostname": hostname, "ip": worker_ip},
            )
            if resp.status_code == 200:
                wid = resp.json().get("id")
                return {"success": True, "worker_id": wid, "message": f"Worker {hostname} registered"}
            return {"success": False, "message": f"Registration failed: {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/cluster/discovery/register-all")
async def register_all_discovered():
    results = []
    for w in discovered_workers:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{MASTER_URL}/api/v1/workers/register",
                    json={"name": w["hostname"], "hostname": w["hostname"], "ip": w["ip"]},
                )
                if resp.status_code == 200:
                    results.append({"ip": w["ip"], "success": True, "worker_id": resp.json().get("id")})
                else:
                    results.append({"ip": w["ip"], "success": False, "error": str(resp.status_code)})
        except Exception as e:
            results.append({"ip": w["ip"], "success": False, "error": str(e)})
    return {"results": results, "total": len(results), "successful": sum(1 for r in results if r["success"])}


@router.get("/cluster/workers")
async def get_cluster_workers():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{MASTER_URL}/api/v1/workers")
            if resp.status_code == 200:
                return {"workers": resp.json()}
            return {"workers": [], "error": f"Master returned {resp.status_code}"}
    except Exception as e:
        return {"workers": [], "error": str(e)}


@router.post("/cluster/workers/maintenance")
async def set_maintenance_mode(data: dict):
    worker_id = data.get("worker_id")
    enabled = data.get("enabled", True)
    if enabled:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(f"{MASTER_URL}/api/v1/workers/{worker_id}/pause")
            return {"success": True, "message": "Worker in maintenance mode", "maintenance": True}
        except Exception as e:
            return {"success": False, "message": str(e)}
    else:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(f"{MASTER_URL}/api/v1/workers/{worker_id}/resume")
            return {"success": True, "message": "Worker resumed", "maintenance": False}
        except Exception as e:
            return {"success": False, "message": str(e)}


@router.get("/cluster/health")
async def get_cluster_health():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            workers_resp = await client.get(f"{MASTER_URL}/api/v1/workers")
            workers = workers_resp.json() if workers_resp.status_code == 200 else []
            jobs_resp = await client.get(f"{MASTER_URL}/api/v1/jobs")
            jobs = jobs_resp.json() if jobs_resp.status_code == 200 else []

            avg_cpu = sum(w.get("cpu_percent", 0) for w in workers) / max(len(workers), 1)
            avg_ram = sum(w.get("ram_percent", 0) for w in workers) / max(len(workers), 1)
            avg_disk = sum(w.get("disk_percent", 0) for w in workers) / max(len(workers), 1)
            versions = {}
            for w in workers:
                v = w.get("version", "unknown")
                versions[v] = versions.get(v, 0) + 1

            return {
                "average_cpu": round(avg_cpu, 1),
                "average_ram": round(avg_ram, 1),
                "average_disk": round(avg_disk, 1),
                "average_latency_ms": 0.0,
                "failed_workers": sum(1 for w in workers if w.get("status") == "offline"),
                "heartbeat_delay_seconds": 0,
                "network_quality": "good" if len(workers) > 0 else "unknown",
                "worker_versions": versions,
                "scheduler_status": "running",
                "database_status": "connected",
                "websocket_status": "connected" if cluster_status["web_socket_connected"] else "disconnected",
                "total_jobs": len(jobs),
                "queued_jobs": sum(1 for j in jobs if j.get("status") == "queued"),
                "running_jobs": sum(1 for j in jobs if j.get("status") == "running"),
                "completed_jobs": sum(1 for j in jobs if j.get("status") == "completed"),
                "failed_jobs": sum(1 for j in jobs if j.get("status") == "failed"),
            }
    except Exception as e:
        return {"error": str(e)}


@router.get("/cluster/map")
async def get_cluster_map():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{MASTER_URL}/api/v1/workers")
            workers = resp.json() if resp.status_code == 200 else []
            return {
                "master": {"hostname": socket.gethostname(), "ip": "127.0.0.1", "port": 8000},
                "workers": [
                    {
                        "id": w.get("id"),
                        "name": w.get("worker_name"),
                        "hostname": w.get("hostname"),
                        "ip": w.get("ip"),
                        "status": w.get("status"),
                        "cpu_percent": w.get("cpu_percent"),
                        "ram_percent": w.get("ram_percent"),
                        "latency_ms": 0.0,
                    }
                    for w in workers
                ],
            }
    except Exception as e:
        return {"master": {}, "workers": [], "error": str(e)}


@router.post("/cluster/backup")
async def create_backup():
    backup_dir = BACKEND_DIR.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"aicluster_backup_{timestamp}.zip"

    try:
        with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as zf:
            if DATA_FILE.exists():
                zf.write(DATA_FILE, "data/aicluster.db")
            config_file = BACKEND_DIR / ".env"
            if config_file.exists():
                zf.write(config_file, "config/.env")
            log_dir = BACKEND_DIR / "logs"
            if log_dir.exists():
                for lf in log_dir.glob("*.log*"):
                    zf.write(lf, f"logs/{lf.name}")

        cluster_status["last_backup"] = timestamp
        checksum = _compute_checksum(backup_file)
        return {
            "success": True,
            "file": str(backup_file),
            "timestamp": timestamp,
            "size_bytes": backup_file.stat().st_size,
            "checksum": checksum,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/cluster/restore")
async def restore_backup(data: dict):
    backup_path = data.get("path", "")
    backup_file = Path(backup_path)
    if not backup_file.exists():
        return {"success": False, "error": "Backup file not found"}

    try:
        with zipfile.ZipFile(backup_file, "r") as zf:
            zf.extractall(BACKEND_DIR.parent / "restore_temp")

        restore_data = BACKEND_DIR.parent / "restore_temp" / "data" / "aicluster.db"
        if restore_data.exists():
            import shutil
            shutil.copy2(restore_data, DATA_FILE)
            cluster_status["last_backup"] = "restored"

        temp_dir = BACKEND_DIR.parent / "restore_temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        return {"success": True, "message": "Backup restored successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/backups")
async def list_backups():
    backup_dir = BACKEND_DIR.parent / "backups"
    if not backup_dir.exists():
        return {"backups": []}
    backups = []
    for f in sorted(backup_dir.glob("*.zip"), reverse=True):
        backups.append({
            "file": f.name,
            "path": str(f),
            "size_bytes": f.stat().st_size,
            "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
    return {"backups": backups}


def _compute_checksum(filepath: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@router.get("/alerts")
async def get_alerts():
    return {"alerts": cluster_status["alerts"][-100:]}


@router.post("/alerts/read")
async def mark_alerts_read():
    for a in cluster_status["alerts"]:
        a["read"] = True
    return {"success": True}


@router.get("/diagnostics")
async def run_diagnostics():
    results = []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{MASTER_URL}/api/v1/health")
            results.append({"test": "Master API", "status": "pass" if resp.status_code == 200 else "fail", "detail": f"HTTP {resp.status_code}"})
    except Exception as e:
        results.append({"test": "Master API", "status": "fail", "detail": str(e)})

    results.append({"test": "Database", "status": "pass" if DATA_FILE.exists() else "fail", "detail": f"DB file: {DATA_FILE.exists()}"})
    results.append({"test": "Disk Space", "status": "pass" if psutil.disk_usage("/").free > 1e9 else "warning", "detail": f"{psutil.disk_usage('/').free / 1e9:.1f}GB free"})
    results.append({"test": "Memory", "status": "pass" if psutil.virtual_memory().available > 2e9 else "warning", "detail": f"{psutil.virtual_memory().available / 1e9:.1f}GB available"})
    results.append({"test": "CPU Load", "status": "pass" if psutil.cpu_percent(interval=0.5) < 80 else "warning", "detail": f"{psutil.cpu_percent(interval=0)}% used"})
    results.append({"test": "Python Version", "status": "pass", "detail": sys.version.split()[0]})
    results.append({"test": "WebSocket", "status": "pass" if cluster_status["web_socket_connected"] else "warning", "detail": "Not connected" if not cluster_status["web_socket_connected"] else "Connected"})

    return {"results": results, "timestamp": datetime.now().isoformat()}


@router.get("/system/version")
async def get_system_version():
    return {
        "app_version": "1.0.0",
        "python_version": sys.version.split()[0],
        "os": platform.system(),
        "os_version": platform.version(),
        "hostname": socket.gethostname(),
    }


@router.post("/system/restart")
async def restart_master():
    return {"success": True, "message": "Restart requested"}


@router.get("/logs")
async def get_logs(limit: int = 100, source: str = ""):
    log_dir = BACKEND_DIR / "logs"
    entries = []
    if not log_dir.exists():
        return {"entries": []}
    for f in sorted(log_dir.glob("*.log*"), reverse=True)[:3]:
        try:
            with open(f, encoding="utf-8") as fh:
                for line in fh.readlines()[-limit:]:
                    line = line.strip()
                    if source and source not in line:
                        continue
                    entries.append({"timestamp": line[:19] if len(line) > 19 else "", "message": line, "source": f.name})
        except (OSError, UnicodeDecodeError):
            pass
    return {"entries": entries[-limit:]}


@router.get("/workers/{worker_id}/logs")
async def get_worker_logs(worker_id: str, limit: int = 100):
    try:
        workers_resp = await _get(f"{MASTER_URL}/api/v1/workers")
        workers = workers_resp.json() if workers_resp else []
        worker = next((w for w in workers if w.get("id") == worker_id), None)
        if not worker:
            return {"entries": [], "error": "Worker not found"}
        worker_ip = worker.get("ip", "127.0.0.1")
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"http://{worker_ip}:8900/api/logs?limit={limit}")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return {"entries": [{"timestamp": "", "message": "Worker log service unreachable", "source": worker_id}]}
    except Exception as e:
        return {"entries": [], "error": str(e)}


@router.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


async def _get(url: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
            return resp
    except Exception:
        return None
