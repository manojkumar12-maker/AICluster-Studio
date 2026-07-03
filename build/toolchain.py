"""Tool detection helpers used by verify.py and the orchestrator.

Every function returns a small dataclass describing whether the tool is
present, its version, and (when relevant) the path to the executable.
The build system never assumes any tool is installed — it always asks.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class ToolStatus:
    name: str
    available: bool
    version: str = ""
    path: Optional[str] = None
    required: bool = True
    min_version: Optional[Tuple[int, ...]] = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "available": self.available,
            "version": self.version,
            "path": self.path,
            "required": self.required,
            "min_version": list(self.min_version) if self.min_version else None,
            "notes": self.notes,
        }


def _run(cmd: List[str], timeout: int = 15) -> Tuple[bool, str, str]:
    """Execute ``cmd`` and capture stdout/stderr.

    On Windows, executable shims with ``.cmd`` / ``.bat`` extensions need
    to be invoked through ``cmd.exe`` or with ``shell=True`` — otherwise
    ``subprocess`` raises ``OSError: [WinError 193]``. We try the direct
    form first and fall back to ``shell=True`` if that fails.
    """
    import os
    use_shell = False
    if os.name == "nt" and cmd:
        exe = shutil.which(cmd[0]) or cmd[0]
        if exe.lower().endswith((".cmd", ".bat")):
            use_shell = True
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=use_shell,
        )
        return (
            completed.returncode == 0,
            (completed.stdout or "").strip(),
            (completed.stderr or "").strip(),
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return False, "", str(exc)


def _parse_version(text: str) -> str:
    for token in text.replace("\n", " ").split():
        if token and token[0].isdigit():
            cleaned = token.strip(",;).")
            return cleaned
    return text.strip().splitlines()[0] if text.strip() else "unknown"


def _version_tuple(text: str) -> Optional[Tuple[int, ...]]:
    import re

    m = re.search(r"(\d+(?:\.\d+){0,3})", text)
    if not m:
        return None
    parts: List[int] = []
    for chunk in m.group(1).split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            break
    return tuple(parts) if parts else None


def check_python(required: Tuple[int, int] = (3, 12)) -> ToolStatus:
    ok, out, err = _run([sys_executable(), "--version"])  # type: ignore[arg-type]
    version = _parse_version(out or err)
    tup = _version_tuple(version)
    ok = ok and tup is not None and tup >= tuple(required)
    return ToolStatus(
        name="Python",
        available=ok,
        version=version,
        path=sys_executable(),
        min_version=required,
        notes="python interpreter" if ok else "minimum not satisfied",
    )


def check_node(required: Tuple[int, int] = (18, 0)) -> ToolStatus:
    path = shutil.which("node")
    if not path:
        return ToolStatus(
            name="Node.js", available=False, min_version=required,
            notes="not found on PATH",
        )
    ok, out, err = _run(["node", "--version"])
    version = _parse_version(out or err).lstrip("v")
    tup = _version_tuple(version)
    available = ok and tup is not None and tup >= tuple(required)
    return ToolStatus(
        name="Node.js", available=available, version=version, path=path,
        min_version=required,
    )


def check_npm(required: Optional[Tuple[int, int]] = None) -> ToolStatus:
    path = shutil.which("npm")
    if not path:
        return ToolStatus(name="npm", available=False, min_version=required,
                          notes="not found on PATH")
    ok, out, err = _run(["npm", "--version"])
    version = _parse_version(out or err)
    return ToolStatus(name="npm", available=ok, version=version, path=path,
                      min_version=required)


def check_cargo(required: Tuple[int, int] = (1, 70)) -> ToolStatus:
    path = shutil.which("cargo")
    if not path:
        return ToolStatus(name="Rust/Cargo", available=False,
                          min_version=required, notes="not found on PATH",
                          required=False)
    ok, out, err = _run(["cargo", "--version"])
    version = _parse_version(out or err)
    tup = _version_tuple(version)
    available = ok and tup is not None and tup >= tuple(required)
    return ToolStatus(
        name="Rust/Cargo", available=available, version=version, path=path,
        min_version=required, required=False,
    )


def check_rustc(required: Tuple[int, int] = (1, 70)) -> ToolStatus:
    path = shutil.which("rustc")
    if not path:
        return ToolStatus(name="rustc", available=False, min_version=required,
                          required=False, notes="not found on PATH")
    ok, out, err = _run(["rustc", "--version"])
    version = _parse_version(out or err)
    return ToolStatus(name="rustc", available=ok, version=version, path=path,
                      min_version=required, required=False)


def check_tauri(required: Tuple[int, int] = (2, 0)) -> ToolStatus:
    """Detect the Tauri v2 CLI (``cargo tauri`` or ``tauri``)."""
    for cmd in (["cargo", "tauri", "--version"], ["tauri", "--version"]):
        ok, out, err = _run(cmd)
        if ok:
            version = _parse_version(out or err)
            tup = _version_tuple(version)
            available = tup is not None and tup >= tuple(required)
            return ToolStatus(
                name="Tauri CLI", available=available, version=version,
                min_version=required, required=False,
                notes=f"via {' '.join(cmd)}",
            )
    return ToolStatus(name="Tauri CLI", available=False, min_version=required,
                      required=False, notes="not installed")


def check_pyinstaller() -> ToolStatus:
    path = shutil.which("pyinstaller")
    if not path:
        # fall back to python -m
        ok, out, err = _run(
            [sys_executable(), "-m", "PyInstaller", "--version"]
        )
        if ok:
            version = _parse_version(out or err)
            return ToolStatus(
                name="PyInstaller", available=True, version=version,
                path=sys_executable(), notes="python -m PyInstaller",
            )
        return ToolStatus(
            name="PyInstaller", available=False,
            notes="install with: pip install pyinstaller",
        )
    ok, out, err = _run(["pyinstaller", "--version"])
    version = _parse_version(out or err)
    return ToolStatus(name="PyInstaller", available=ok, version=version, path=path)


def check_inno_setup() -> ToolStatus:
    """Locate the Inno Setup compiler (ISCC.exe) on Windows."""
    candidates: List[Path] = []
    if path := shutil.which("iscc"):
        candidates.append(Path(path))
    for env in ("ProgramFiles(x86)", "ProgramFiles"):
        base = Path(os.environ.get(env, str(Path.home() / env)))
        if not base.exists():
            continue
        for sub in ("Inno Setup 6", "Inno Setup"):
            target = base / sub
            if target.exists():
                for found in target.glob("ISCC.exe"):
                    candidates.append(found)
    if not candidates:
        return ToolStatus(
            name="Inno Setup", available=False, required=False,
            notes="install Inno Setup 6 to produce installers",
        )
    exe = candidates[0]
    return ToolStatus(
        name="Inno Setup", available=True, version="detected", path=str(exe),
        required=False,
    )


def check_7z() -> ToolStatus:
    path = shutil.which("7z") or shutil.which("7z.exe")
    return ToolStatus(
        name="7-Zip", available=bool(path), path=path, required=False,
        notes="optional, used for portable ZIPs",
    )


def check_signtool() -> ToolStatus:
    """Look for the Windows signtool (part of the Windows SDK)."""
    candidates: List[Path] = []
    if path := shutil.which("signtool"):
        candidates.append(Path(path))
    for env in ("ProgramFiles(x86)", "ProgramFiles"):
        base = Path.home().joinpath(env, "Windows Kits")
        if base.exists():
            for found in base.rglob("signtool.exe"):
                candidates.append(found)
    if not candidates:
        return ToolStatus(
            name="signtool", available=False, required=False,
            notes="optional, install Windows SDK for code signing",
        )
    return ToolStatus(
        name="signtool", available=True, version="detected",
        path=str(candidates[0]), required=False,
    )


def sys_executable() -> str:
    import sys
    return sys.executable


def gather_all() -> List[ToolStatus]:
    return [
        check_python(),
        check_node(),
        check_npm(),
        check_cargo(),
        check_rustc(),
        check_tauri(),
        check_pyinstaller(),
        check_inno_setup(),
        check_7z(),
        check_signtool(),
    ]


if __name__ == "__main__":
    print(json.dumps([s.to_dict() for s in gather_all()], indent=2))
