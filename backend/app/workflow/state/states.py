WORKFLOW_STATES = [
    "PENDING", "VALIDATING", "PLANNING", "QUEUED",
    "DISPATCHING", "RUNNING", "WAITING", "MERGING",
    "COMPLETED", "FAILED", "CANCELLED", "TIMEOUT",
    "RETRYING", "ARCHIVED",
]

TASK_STATES = [
    "CREATED", "READY", "ASSIGNED", "RUNNING",
    "WAITING", "SUCCESS", "FAILED", "RETRY",
    "SKIPPED", "CANCELLED",
]

TASK_TYPES = [
    "echo", "sleep", "dir_scan", "hash_file", "count_files",
    "compress", "extract", "report", "custom",
]

VALID_TRANSITIONS: dict[str, list[str]] = {
    "CREATED": ["READY", "CANCELLED"],
    "READY": ["ASSIGNED", "FAILED", "CANCELLED"],
    "ASSIGNED": ["RUNNING", "FAILED", "CANCELLED"],
    "RUNNING": ["SUCCESS", "FAILED", "RETRY", "CANCELLED"],
    "WAITING": ["READY", "FAILED", "CANCELLED"],
    "SUCCESS": [],
    "FAILED": ["RETRY", "CANCELLED"],
    "RETRY": ["READY", "CANCELLED"],
    "SKIPPED": [],
    "CANCELLED": [],
}


def is_valid_task_transition(current: str, next_state: str) -> bool:
    allowed = VALID_TRANSITIONS.get(current, [])
    return next_state in allowed
