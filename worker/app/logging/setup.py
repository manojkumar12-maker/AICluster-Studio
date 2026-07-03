import logging
import os
from logging.handlers import RotatingFileHandler

from ..core.constants import MAX_LOG_SIZE_BYTES, LOG_BACKUP_COUNT


def setup_worker_logging(log_dir: str = "logs", log_level: str = "INFO"):
    os.makedirs(log_dir, exist_ok=True)

    log_format = (
        "%(asctime)s [%(levelname)s] "
        "worker_id=%(worker_id)s job_id=%(job_id)s "
        "%(message)s"
    )

    class WorkerAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            extra = kwargs.get("extra", {})
            worker_id = extra.get("worker_id", "-")
            job_id = extra.get("job_id", "-")
            return (
                f"%(asctime)s [%(levelname)s] "
                f"worker_id={worker_id} job_id={job_id} "
                f"{msg}",
                kwargs,
            )

    class WorkerFormatter(logging.Formatter):
        def format(self, record):
            if not hasattr(record, "worker_id"):
                record.worker_id = "-"
            if not hasattr(record, "job_id"):
                record.job_id = "-"
            return super().format(record)

    formatter = WorkerFormatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    log_file = os.path.join(log_dir, "worker.log")
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except (OSError, PermissionError):
        pass

    for noisy_logger in ("httpx", "httpcore", "urllib3"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
