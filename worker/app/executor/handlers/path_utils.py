import os


def validate_path(path: str, allowed_directories: list[str] | None = None) -> str:
    if not path:
        raise ValueError("Path is required")

    if not os.path.isabs(path):
        raise ValueError("Path must be absolute")

    normalized = os.path.normpath(path)
    parts = normalized.split(os.sep)
    if ".." in parts:
        raise ValueError("Directory traversal not allowed")

    if allowed_directories:
        allowed = False
        for allowed_dir in allowed_directories:
            norm_allowed = os.path.normpath(allowed_dir)
            if normalized.startswith(norm_allowed):
                allowed = True
                break
        if not allowed:
            raise ValueError(
                f"Path must be within allowed directories: {allowed_directories}"
            )

    return normalized
