"""Bootstrap wrappers used as PyInstaller entry points.

These wrappers exist so the PyInstaller-frozen binaries can resolve
relative imports (e.g. ``from .config import settings`` in
``backend/app/main.py``) without modifying the application code.

When PyInstaller sees a script as the entry, it runs it as
``__main__`` with no parent package, so relative imports break. We
work around that by importing the application module and calling its
top-level functions - which executes the application as part of its
real package.

This file is part of the build system and is **not** application
code; it only contains build-time glue.
"""

from __future__ import annotations

import sys


def main() -> None:
    """Bootstrap the AICluster Master service."""
    # When PyInstaller extracts the bundle, the application package
    # is laid out under ``app/`` in the extraction directory. We add
    # the parent directory to ``sys.path`` so that
    # ``import app.main`` works even when the bootloader has not
    # done it for us.
    import os
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and os.path.isdir(os.path.join(meipass, "app")):
        sys.path.insert(0, meipass)
    from app.main import app
    import uvicorn
    uvicorn.run(
        app,
        host=os.environ.get("AICLUSTER_HOST", "127.0.0.1"),
        port=int(os.environ.get("AICLUSTER_API_PORT", "8000")),
        log_level=os.environ.get("AICLUSTER_LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()
