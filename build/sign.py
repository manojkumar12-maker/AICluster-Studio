"""Optional Authenticode code signing.

Signing is intentionally opt-in. The build system never fails a build
just because the binary isn't signed — it only emits warnings. To
enable signing, set:

    AICLUSTER_SIGNTOOL_PATH  (path to signtool.exe)
    AICLUSTER_CERT_PATH      (path to .pfx / .p12)
    AICLUSTER_CERT_PASSWORD  (certificate password, or use a CSP)

…and pass ``--sign`` to ``build.py``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .config import BuildConfig
from .logger import setup_logging, get_logger

log = get_logger("aicluster.build.sign")


@dataclass
class SignResult:
    file: Path
    signed: bool
    message: str = ""


def _resolve_signtool() -> Optional[str]:
    explicit = os.environ.get("AICLUSTER_SIGNTOOL_PATH")
    if explicit and Path(explicit).exists():
        return explicit
    on_path = shutil.which("signtool")
    return on_path


def is_available() -> bool:
    return _resolve_signtool() is not None


def sign_file(path: Path, cfg: Optional[BuildConfig] = None) -> SignResult:
    cfg = cfg or BuildConfig()
    tool = _resolve_signtool()
    if not tool:
        msg = "signtool not available — skipping"
        log.warning("[%s] %s", path.name, msg)
        return SignResult(file=path, signed=False, message=msg)

    cert = os.environ.get("AICLUSTER_CERT_PATH")
    password = os.environ.get("AICLUSTER_CERT_PASSWORD", "")
    if not cert or not Path(cert).exists():
        msg = "AICLUSTER_CERT_PATH not set — skipping"
        log.warning("[%s] %s", path.name, msg)
        return SignResult(file=path, signed=False, message=msg)

    cmd: List[str] = [
        tool, "sign",
        "/fd", "SHA256",
        "/td", "SHA256",
        "/tr", "http://timestamp.digicert.com",
        "/f", cert,
    ]
    if password:
        cmd += ["/p", password]
    cmd.append(str(path))

    log.info("[%s] signing with %s", path.name, tool)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        log.error("[%s] sign failed: %s", path.name, proc.stderr.strip())
        return SignResult(file=path, signed=False, message=proc.stderr.strip())
    log.info("[%s] signed", path.name)
    return SignResult(file=path, signed=True)


def sign_directory(directory: Path, cfg: Optional[BuildConfig] = None) -> List[SignResult]:
    cfg = cfg or BuildConfig()
    if cfg.skip_sign:
        log.info("signing skipped (config)")
        return []
    if not directory.exists():
        return []
    results: List[SignResult] = []
    for exe in sorted(directory.glob("*.exe")):
        results.append(sign_file(exe, cfg))
    return results


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "release")
    for r in sign_directory(target):
        print(r)
