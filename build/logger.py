"""Centralised logging for the build system.

Writes to both stdout and ``logs/build.log`` so that the orchestrator
always has a persistent record of what ran.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .config import LOGS_DIR


_FMT = "%(asctime)s [%(levelname)-7s] %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


_initialised = False


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """Configure the root logger and return a build-specific child logger.

    Idempotent — calling it twice does not double-up handlers.
    """
    global _initialised

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if log_file is None:
        log_file = LOGS_DIR / "build.log"

    root = logging.getLogger("aicluster.build")
    if _initialised:
        root.setLevel(level.upper())
        return root

    root.setLevel(level.upper())
    root.propagate = False

    stream = logging.StreamHandler(stream=sys.stdout)
    stream.setFormatter(logging.Formatter(_FMT, _DATEFMT))
    root.addHandler(stream)

    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(_FMT, _DATEFMT))
        root.addHandler(file_handler)
    except OSError:
        # Non-fatal: the build can still log to stdout.
        pass

    _initialised = True
    return root


def get_logger(name: str = "aicluster.build") -> logging.Logger:
    return logging.getLogger(name)
