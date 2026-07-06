"""Tauri v2 build orchestration.

Builds the three Tauri v2 desktop applications:

    * Master Control Center
    * Worker Control Center
    * AICluster Studio

The build is real - we run ``npm install``, ``npm run build`` and
finally ``cargo tauri build``. There are no placeholder executables,
no mock binaries, and no fallback that copies an arbitrary file as
the produced Tauri EXE. If any step fails, the build aborts and the
real error is reported.

The build host must have:

    * Node.js 18+ and npm
    * Rust 1.70+ and Cargo
    * The Tauri CLI (``cargo install tauri-cli --version "^2.0"``)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .config import ICONS_DIR, RELEASE_DIR, TAURI_TARGETS, BuildConfig
from .logger import setup_logging, get_logger
from .version import VersionInfo, resolve_version

log = get_logger("aicluster.build.tauri")


CARGO_TOML = """[package]
name = "{app_name}"
version = "{version}"
description = "{description}"
authors = ["{company}"]
edition = "2021"
rust-version = "1.70"

[[bin]]
name = "{binary_name}"
path = "src/main.rs"

[lib]
name = "{app_name}_lib"
crate-type = ["staticlib", "cdylib", "rlib"]

[build-dependencies]
tauri-build = {{ version = "2.0", features = [] }}

[dependencies]
tauri = {{ version = "2.0", features = [] }}
serde = {{ version = "1", features = ["derive"] }}
serde_json = "1"
"""

BUILD_RS = """fn main() {
    tauri_build::build()
}
"""

MAIN_RS = """fn main() {{
    {app_name}_lib::run()
}}
"""

LIB_RS = """#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {{
    tauri::Builder::default()
        .setup(|_app| Ok(()))
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}}
"""

TAURI_CONF_JSON = """{{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "{product_name}",
  "version": "{version}",
  "identifier": "com.aicluster.{app_key}",
  "build": {{
    "beforeDevCommand": "",
    "devUrl": "http://localhost:{dev_port}",
    "beforeBuildCommand": "npm run build",
    "frontendDist": "../dist"
  }},
  "app": {{
    "windows": [
      {{
        "title": "{product_name}",
        "width": 1280,
        "height": 800,
        "minWidth": 960,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false
      }}
    ],
    "security": {{
      "csp": null
    }}
  }},
  "bundle": {{
    "active": true,
    "targets": ["nsis"],
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.ico"
    ],
    "category": "DeveloperTool",
    "copyright": "{copyright}",
    "shortDescription": "{description}",
    "longDescription": "{description}"
  }}
}}
"""

CAPABILITIES_JSON = """{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "default capabilities",
  "windows": ["main"],
  "permissions": [
    "core:default"
  ]
}
"""

GITIGNORE = """target/
gen/schemas/
"""


def _ensure_icons(src_tauri: Path) -> None:
    """Copy icon assets into the Tauri project. Fails on missing icons."""
    icons = src_tauri / "icons"
    icons.mkdir(parents=True, exist_ok=True)
    required = ("32x32.png", "128x128.png", "128x128@2x.png", "icon.ico")
    for name in required:
        candidate = ICONS_DIR / name
        if not candidate.exists():
            candidate = ICONS_DIR / "default.ico"
        if not candidate.exists():
            raise RuntimeError(
                f"required Tauri icon missing: {name} "
                f"(no default fallback at {ICONS_DIR / 'default.ico'})"
            )
        dest = icons / name
        if not dest.exists():
            shutil.copy2(candidate, dest)


def scaffold(target, version: VersionInfo) -> Path:
    """Create the ``src-tauri/`` directory for ``target``.

    Only files the build will not generate are scaffolded; everything
    that is generated lives in the same tree but is rebuilt each run.
    """
    src_tauri = target.tauri_config_dir
    src_tauri.mkdir(parents=True, exist_ok=True)

    app_key = target.key.replace("-", "_")
    binary_name = target.output_name.replace(".exe", "").replace(" ", "")

    (src_tauri / "Cargo.toml").write_text(
        CARGO_TOML.format(
            app_name=app_key,
            binary_name=binary_name,
            version=version.version,
            description=target.description,
            company=version.company,
        ),
        encoding="utf-8",
    )
    (src_tauri / "build.rs").write_text(BUILD_RS, encoding="utf-8")

    src_dir = src_tauri / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "main.rs").write_text(
        MAIN_RS.format(app_name=app_key), encoding="utf-8"
    )
    (src_dir / "lib.rs").write_text(LIB_RS, encoding="utf-8")

    capabilities = src_tauri / "capabilities"
    capabilities.mkdir(exist_ok=True)
    (capabilities / "default.json").write_text(
        CAPABILITIES_JSON, encoding="utf-8"
    )

    (src_tauri / ".gitignore").write_text(GITIGNORE, encoding="utf-8")

    (src_tauri / "tauri.conf.json").write_text(
        TAURI_CONF_JSON.format(
            product_name=target.name,
            version=version.version,
            app_key=app_key.replace("_", "-"),
            dev_port="5174",
            copyright=version.copyright,
            description=target.description,
        ),
        encoding="utf-8",
    )

    _ensure_icons(src_tauri)
    log.info("scaffolded Tauri project: %s", src_tauri)
    return src_tauri


def _resolve_npm() -> List[str]:
    """Return the command prefix to invoke npm reliably on Windows.

    On Windows, ``npm`` resolves itself by reading the project-local
    ``node_modules\\npm\\bin\\npm-cli.js`` first. When this file is
    missing (because the user ran ``npm install`` once and the project
    cache was cleared), the second invocation of ``npm run`` fails.
    To avoid this, we always invoke ``npm.cmd`` through cmd.exe.
    """
    if os.name == "nt":
        npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
        if npm_cmd and npm_cmd.lower().endswith(".cmd"):
            return ["cmd.exe", "/c", npm_cmd]
    npm = shutil.which("npm")
    if npm:
        return [npm]
    raise RuntimeError("npm is not installed on PATH")


def _run(cmd: List[str], cwd: Path) -> int:
    log.info("$ %s (cwd=%s)", " ".join(cmd), cwd)
    # Inject the user's cargo bin dir on Windows so that rustup-style
    # toolchains (which are not on PATH by default) can be found.
    if os.name == "nt":
        cargo_bin = Path.home() / ".cargo" / "bin"
        if cargo_bin.exists():
            new_cmd = []
            for c in cmd:
                if (cargo_bin / c).exists():
                    new_cmd.append(str(cargo_bin / c))
                elif (cargo_bin / (c + ".exe")).exists():
                    new_cmd.append(str(cargo_bin / (c + ".exe")))
                else:
                    new_cmd.append(c)
            cmd = new_cmd
    needs_shell = _needs_shell(cmd)
    if needs_shell:
        proc = subprocess.run(
            " ".join(f'"{c}"' for c in cmd),
            cwd=cwd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
    else:
        proc = subprocess.run(
            cmd, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
    if proc.stdout:
        for line in proc.stdout.splitlines():
            log.info("  | %s", line)
    return proc.returncode


def _needs_shell(cmd: List[str]) -> bool:
    """Return True if the command must be invoked through a shell."""
    if not cmd or os.name != "nt":
        return False
    exe = cmd[0]
    lower = exe.lower()
    if lower.endswith((".cmd", ".bat")):
        return True
    if Path(exe).suffix == "" and not Path(exe).exists():
        return True
    return False


def _required_exe(release_dir: Path, expected_name: str) -> Path:
    """Return the path to the produced Tauri executable or raise."""
    candidate = release_dir / expected_name
    if not candidate.exists():
        raise RuntimeError(
            f"tauri build did not produce {expected_name} "
            f"in {release_dir}. Expected output is missing."
        )
    size = candidate.stat().st_size
    if size < 1024:
        raise RuntimeError(
            f"tauri build produced {candidate} but it is suspiciously "
            f"small ({size} bytes); aborting."
        )
    return candidate


def build_target(target, version: VersionInfo, cfg: BuildConfig) -> Path:
    """Build one Tauri target. Raises on any failure.

    Returns the path of the published executable in
    ``release/<subdir>/<exe>``. Never returns a path to a placeholder,
    mock or stub binary.
    """
    if cfg.skip_tauri:
        raise RuntimeError(
            f"--skip-tauri is set; cannot build {target.name}. "
            f"Run the build without this flag to produce real Tauri EXEs."
        )

    src_tauri = scaffold(target, version)

    log.info("[%s] installing frontend dependencies", target.name)
    npm = _resolve_npm()
    needs_install = (
        not (target.frontend_dir / "node_modules").exists()
        or not (target.frontend_dir / "node_modules" / ".package-lock.json").exists()
    )
    if needs_install:
        if _run(npm + ["install"], cwd=target.frontend_dir) != 0:
            if _run(npm + ["ci"], cwd=target.frontend_dir) != 0:
                raise RuntimeError(
                    f"frontend npm install failed for {target.name}"
                )

    log.info("[%s] building frontend bundle", target.name)
    if not (target.frontend_dir / "dist").exists():
        if _run(npm + ["run", "build"], cwd=target.frontend_dir) != 0:
            raise RuntimeError(f"frontend build failed for {target.name}")

    log.info("[%s] running tauri build", target.name)
    if _run(["cargo", "tauri", "build", "--no-bundle"], cwd=src_tauri) != 0:
        raise RuntimeError(f"cargo tauri build failed for {target.name}")

    release_dir = src_tauri / "target" / "release"
    if not release_dir.exists():
        raise RuntimeError(
            f"tauri build did not produce target/release at {release_dir}"
        )

    src_exe = _required_exe(release_dir, target.output_name)

    dest_dir = RELEASE_DIR / target.output_subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / target.output_name
    shutil.copy2(src_exe, dest)
    log.info("placed %s -> %s", src_exe, dest)
    return dest


def build_all(cfg: Optional[BuildConfig] = None) -> Dict[str, dict]:
    """Build every Tauri target. Aborts on the first failure."""
    cfg = cfg or BuildConfig()
    setup_logging(cfg.log_level)
    version = resolve_version()
    results: Dict[str, dict] = {}
    for target in TAURI_TARGETS:
        log.info("=== %s ===", target.name)
        try:
            path = build_target(target, version, cfg)
            results[target.key] = {
                "name": target.name,
                "ok": True,
                "path": str(path),
                "output": target.output_name,
                "subdir": target.output_subdir,
                "error": "",
            }
        except Exception as exc:
            log.error("[%s] build failed: %s", target.name, exc)
            results[target.key] = {
                "name": target.name,
                "ok": False,
                "path": None,
                "output": target.output_name,
                "subdir": target.output_subdir,
                "error": str(exc),
            }
    return results


if __name__ == "__main__":
    import sys
    import json
    res = build_all()
    print(json.dumps(res, indent=2))
    sys.exit(0 if all(r["ok"] for r in res.values()) else 1)
