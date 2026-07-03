"""Entry point for the standalone ``aicluster`` CLI.

This module is referenced by :data:`build.config.PYINSTALLER_TARGETS`. It
imports the shared protocol library (no application logic) and exposes a
small ``main()`` function that prints the CLI banner. It is intentionally
tiny so the resulting executable stays small while still demonstrating
the packaging pipeline end-to-end.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# ``sys._MEIPASS`` is set by PyInstaller at runtime and points to the
# temporary directory where bundled assets are extracted.
_BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def _read_manifest() -> dict:
    """Best-effort load of ``config/manifest.json`` if present."""
    candidates = [
        _BUNDLE_ROOT / "config" / "manifest.json",
        _BUNDLE_ROOT.parent / "config" / "manifest.json",
    ]
    for path in candidates:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
    return {}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aicluster",
        description="AICluster command-line interface",
    )
    parser.add_argument("--version", action="store_true", help="print version")
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        help="command to run (default: help)",
    )
    args = parser.parse_args(argv)

    manifest = _read_manifest()
    version = manifest.get("version", "1.2.2")
    name = manifest.get("product_name", "AICluster")

    if args.version or args.command == "version":
        print(f"{name} CLI v{version}")
        return 0
    if args.command in ("help", "-h", "--help"):
        parser.print_help()
        print()
        print("Available subcommands:")
        print("  version         print the CLI version")
        print("  status          print cluster status (stub)")
        print("  help            show this message")
        return 0
    if args.command == "status":
        print(json.dumps({
            "name": name,
            "version": version,
            "status": "stub",
            "note": "real status command is provided by the master server",
        }, indent=2))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
