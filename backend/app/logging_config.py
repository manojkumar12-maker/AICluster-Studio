import logging
import os
from logging.handlers import RotatingFileHandler
from .config import settings


def setup_logging():
    log_format = (
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    formatter = logging.Formatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    log_file = os.path.join(settings.logs_dir, "aicluster.log")
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except (OSError, PermissionError):
        pass

    for logger_name in ("httpx", "httpcore", "aiosqlite"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
