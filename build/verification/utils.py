"""Shared helpers for the AICluster release verification system.

This module centralises the read-only utilities used by every verifier:

    * a per-verifier logger that writes to stdout and ``logs/verification.log``
    * a monotonic :func:`timer` context manager
    * :func:`launch_and_wait` for spawning an executable, observing it for
      a bounded number of seconds, and shutting it down cleanly
    * :func:`http_get` with a timeout, used by the API / health probes
    * :func:`read_pe_metadata` for embedded version info (read-only)

The verification layer never writes to artifacts, never modifies
executables and never touches the database. Every helper here is
designed to be safe to call against a release directory at any time.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..config import LOGS_DIR, REPO_ROOT


_LOG_INITIALISED = False
_LOG_FILE: Optional[Path] = None


def _ensure_logging() -> logging.Logger:
    global _LOG_INITIALISED, _LOG_FILE
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    _LOG_FILE = LOGS_DIR / "verification.log"
    logger = logging.getLogger("aicluster.verification")
    if _LOG_INITIALISED:
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream = logging.StreamHandler(stream=sys.stdout)
        stream.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)-7s] %(name)s | %(message)s",
            "%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(stream)
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        try:
            rotating = logging.handlers.RotatingFileHandler(  # type: ignore[attr-defined]
                _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3,
                encoding="utf-8",
            )
        except Exception:
            from logging.handlers import RotatingFileHandler
            rotating = RotatingFileHandler(
                _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3,
                encoding="utf-8",
            )
        rotating.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)-7s] %(name)s | %(message)s",
            "%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(rotating)
    _LOG_INITIALISED = True
    return logger


def get_logger(name: str = "aicluster.verification") -> logging.Logger:
    """Return the shared verification logger."""
    base = _ensure_logging()
    return base.getChild(name.replace("aicluster.verification.", ""))


@contextlib.contextmanager
def timer(label: str = ""):
    """Context manager that yields the elapsed-seconds callable.

    Usage::

        with timer() as get:
            do_work()
        print(get())   # seconds as float
    """
    start = time.monotonic()
    elapsed = {"value": 0.0}

    def _get() -> float:
        return elapsed["value"]

    try:
        yield _get
    finally:
        elapsed["value"] = time.monotonic() - start


def port_listening(port: int, host: str = "127.0.0.1",
                   timeout: float = 0.5) -> bool:
    """Return True if ``host:port`` accepts a TCP connection within ``timeout``."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def wait_for_port(port: int, *,
                  host: str = "127.0.0.1",
                  deadline_seconds: float = 20.0,
                  poll_interval: float = 0.25) -> bool:
    """Poll for ``host:port`` to start listening. Returns True if it does
    appear within the deadline, False otherwise.
    """
    end = time.monotonic() + deadline_seconds
    while time.monotonic() < end:
        if port_listening(port, host=host, timeout=poll_interval):
            return True
        time.sleep(poll_interval)
    return False


def http_get(url: str, *,
             timeout: float = 5.0,
             expected_status: Tuple[int, ...] = (200,)) -> Tuple[int, str]:
    """Issue a GET request and return ``(status_code, body)``.

    Returns ``(-1, error_message)`` on network failure. The body is
    truncated to 4 KiB to keep the verification report small.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            status = resp.getcode()
            body = resp.read(4096).decode("utf-8", errors="replace")
            if status in expected_status:
                return status, body
            return status, body
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read(4096).decode("utf-8", errors="replace")
        except Exception:
            pass
        return exc.code, body
    except (urllib.error.URLError, socket.timeout, OSError) as exc:
        return -1, str(exc)


def launch_executable(exe: Path, *,
                     args: Iterable[str] = (),
                     cwd: Optional[Path] = None,
                     env: Optional[Dict[str, str]] = None) -> subprocess.Popen:
    """Spawn ``exe`` and return the Popen handle.

    The caller is responsible for terminating the process; this helper
    does *not* wait. ``env`` is merged on top of the current environment.
    """
    cmd: List[str] = [str(exe), *args]
    merged = {**os.environ, **(env or {})}
    return subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=merged,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_creation_flags_no_window(),
    )


def _creation_flags_no_window() -> int:
    """Return a ``creationflags`` value that suppresses the console window
    when launching an executable on Windows. Returns 0 on non-Windows.
    """
    if os.name != "nt":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def terminate_process(proc: subprocess.Popen, *,
                      timeout: float = 5.0) -> bool:
    """Try to terminate ``proc`` gracefully, then kill it. Returns True
    if the process has exited within the combined timeout.
    """
    if proc.poll() is not None:
        return True
    try:
        proc.terminate()
        try:
            return proc.wait(timeout=timeout) is not None
        except subprocess.TimeoutExpired:
            pass
    except OSError:
        pass
    try:
        proc.kill()
        try:
            return proc.wait(timeout=timeout) is not None
        except subprocess.TimeoutExpired:
            return False
    except OSError:
        return False


@dataclass
class PEMetadata:
    """Minimal PE header / version info extracted from an .exe."""

    path: Path
    is_pe: bool
    machine: str
    size_bytes: int
    file_version: Optional[str] = None
    product_version: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "is_pe": self.is_pe,
            "machine": self.machine,
            "size_bytes": self.size_bytes,
            "file_version": self.file_version,
            "product_version": self.product_version,
            "company": self.company,
            "description": self.description,
        }


_MACHINES = {
    0x014C: "i386",
    0x0200: "ia64",
    0x8664: "x64",
    0x01C0: "arm",
    0xAA64: "arm64",
}


def read_pe_metadata(path: Path) -> PEMetadata:
    """Best-effort extraction of PE header + version info from a .exe.

    This is purely a read operation - the file is opened, parsed, and
    closed. The function never writes anything to disk.
    """
    size = path.stat().st_size
    meta = PEMetadata(path=path, is_pe=False, machine="unknown", size_bytes=size)
    try:
        with path.open("rb") as fh:
            data = fh.read(2)
            if data != b"MZ":
                return meta
            fh.seek(0x3C)
            pe_offset_bytes = fh.read(4)
            if len(pe_offset_bytes) != 4:
                return meta
            pe_offset = struct.unpack("<I", pe_offset_bytes)[0]
            fh.seek(pe_offset)
            sig = fh.read(4)
            if sig != b"PE\x00\x00":
                return meta
            machine = struct.unpack("<H", fh.read(2))[0]
            meta.machine = _MACHINES.get(machine, f"0x{machine:04x}")
            meta.is_pe = True
    except OSError:
        return meta
    meta.file_version, meta.product_version, meta.company, meta.description = (
        _read_pe_version_info(path)
    )
    return meta


def _read_pe_version_info(path: Path) -> Tuple[Optional[str], Optional[str],
                                                Optional[str], Optional[str]]:
    """Try to extract the VS_FIXEDFILEINFO and StringFileInfo blocks.

    Returns ``(file_version, product_version, company, description)``.
    Any of the values may be None if the resource block is missing.
    """
    try:
        import pefile  # type: ignore
    except ImportError:
        return _read_pe_version_info_naive(path)
    try:
        pe = pefile.PE(str(path))
        file_version = None
        product_version = None
        company = None
        description = None
        if hasattr(pe, "VS_FIXEDFILEINFO"):
            ffi = pe.VS_FIXEDFILEINFO[0] if isinstance(pe.VS_FIXEDFILEINFO, tuple) else pe.VS_FIXEDFILEINFO
            try:
                major = (ffi.FileVersionMS >> 16) & 0xFFFF
                minor = ffi.FileVersionMS & 0xFFFF
                patch = (ffi.FileVersionLS >> 16) & 0xFFFF
                build = ffi.FileVersionLS & 0xFFFF
                file_version = f"{major}.{minor}.{patch}.{build}"
                major = (ffi.ProductVersionMS >> 16) & 0xFFFF
                minor = ffi.ProductVersionMS & 0xFFFF
                patch = (ffi.ProductVersionLS >> 16) & 0xFFFF
                build = ffi.ProductVersionLS & 0xFFFF
                product_version = f"{major}.{minor}.{patch}.{build}"
            except Exception:
                pass
        if hasattr(pe, "FileInfo"):
            for entry in pe.FileInfo:
                for item in getattr(entry, "StringTable", []) or []:
                    entries = item.entries or {}
                    company = entries.get(b"CompanyName", company)
                    description = entries.get(b"FileDescription", description)
                    if isinstance(company, bytes):
                        company = company.decode("utf-8", errors="replace").strip("\x00").strip()
                    if isinstance(description, bytes):
                        description = description.decode("utf-8", errors="replace").strip("\x00").strip()
        return file_version, product_version, company, description
    except Exception:
        return None, None, None, None


def _read_pe_version_info_naive(path: Path) -> Tuple[Optional[str], Optional[str],
                                                Optional[str], Optional[str]]:
    """Fallback that just searches the raw bytes for VERSION metadata.

    Used when ``pefile`` isn't installed. Returns all-None on miss.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return None, None, None, None
    file_version: Optional[str] = None
    product_version: Optional[str] = None
    for needle in (b"FileVersion", b"ProductVersion"):
        idx = data.find(needle)
        if idx != -1:
            window = data[idx:idx + 256]
            text = window.decode("utf-8", errors="replace")
            for line in text.splitlines():
                if needle.decode() in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        value = parts[1].strip().strip("\x00")
                        if needle == b"FileVersion":
                            file_version = value
                        else:
                            product_version = value
                    break
    return file_version, product_version, None, None


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def read_text_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    text = read_text_file(path)
    if text is None:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return {"_root": data}
    except json.JSONDecodeError:
        return None


def free_port(preferred: int) -> int:
    """Return ``preferred`` if it is free, otherwise a random free port."""
    if not port_listening(preferred, timeout=0.1):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def short_path(path: Path, root: Path = REPO_ROOT) -> str:
    """Return ``path`` relative to ``root`` when possible, else absolute."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def truncate(text: str, *, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "\u2026"
