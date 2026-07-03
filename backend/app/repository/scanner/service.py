import hashlib
import logging
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import AsyncIterator

logger = logging.getLogger(__name__)

IGNORED_DIRS = {"node_modules", "venv", ".venv", "dist", "build", "target", ".git", "__pycache__", ".cache", ".idea", ".vscode", "coverage", ".next"}
IGNORED_EXTENSIONS = {".pyc", ".pyo", ".so", ".dll", ".dylib", ".exe", ".bin", ".o", ".obj", ".lib", ".class", ".jar", ".war"}
TEXT_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".yaml", ".yml", ".html", ".css", ".scss", ".less", ".sql", ".sh", ".bat", ".ps1", ".txt", ".cfg", ".ini", ".toml", ".xml", ".svg", ".env", ".gitignore", ".dockerfile", ".conf", ".gradle", ".properties", ".rb", ".php", ".go", ".rs", ".java", ".kt", ".swift", ".c", ".cpp", ".h", ".hpp", ".cs", ".vue", ".svelte", ".astro", ".mjs", ".cjs", ".mts", ".cts", ".d.ts"}
LANGUAGE_MAP = {
    ".py": "python", ".ts": "typescript", ".tsx": "typescript", ".js": "javascript", ".jsx": "javascript",
    ".json": "json", ".md": "markdown", ".yaml": "yaml", ".yml": "yaml", ".html": "html", ".css": "css",
    ".sql": "sql", ".sh": "shell", ".bat": "batch", ".ps1": "powershell", ".toml": "toml", ".xml": "xml",
    ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin", ".swift": "swift", ".rb": "ruby",
    ".php": "php", ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".cs": "csharp",
    ".vue": "vue", ".svelte": "svelte", ".astro": "astro",
}


def detect_language(filepath: str) -> str | None:
    ext = Path(filepath).suffix.lower()
    return LANGUAGE_MAP.get(ext)


def is_binary_file(filepath: str) -> bool:
    ext = Path(filepath).suffix.lower()
    if ext in TEXT_EXTENSIONS:
        return False
    if ext in IGNORED_EXTENSIONS:
        return True
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
            return b"\0" in chunk
    except Exception:
        return True


def should_ignore(rel_path: str) -> bool:
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        if part in IGNORED_DIRS or part.startswith("."):
            return True
    ext = Path(rel_path).suffix.lower()
    return ext in IGNORED_EXTENSIONS


class FileScanner:
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()

    async def scan(self) -> AsyncIterator[dict]:
        for root, dirs, files in os.walk(self.root):
            rel_root = str(Path(root).relative_to(self.root))
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for fname in files:
                fpath = os.path.join(root, fname)
                rel_path = str(Path(fpath).relative_to(self.root))
                if should_ignore(rel_path):
                    continue
                try:
                    stat = os.stat(fpath)
                    lang = detect_language(fpath)
                    binary = is_binary_file(fpath)
                    content_hash = self._hash_file(fpath) if not binary else None
                    lines = 0
                    code_lines = 0
                    comment_lines = 0
                    if not binary:
                        try:
                            with open(fpath, encoding="utf-8", errors="replace") as f:
                                text = f.read()
                            lines = text.count("\n") + 1
                            for line in text.split("\n"):
                                stripped = line.strip()
                                if not stripped:
                                    continue
                                if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*") or stripped.startswith("--"):
                                    comment_lines += 1
                                else:
                                    code_lines += 1
                        except Exception:
                            lines = 0
                    yield {
                        "path": rel_path,
                        "filename": fname,
                        "extension": Path(fname).suffix.lower(),
                        "language": lang,
                        "size_bytes": stat.st_size,
                        "lines": lines,
                        "code_lines": code_lines,
                        "comment_lines": comment_lines,
                        "blank_lines": max(0, lines - code_lines - comment_lines),
                        "hash": content_hash,
                        "is_binary": binary,
                        "is_generated": "generated" in rel_path.lower() or "pb." in fname,
                        "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    }
                except (OSError, PermissionError):
                    continue

    def _hash_file(self, fpath: str) -> str:
        h = hashlib.sha256()
        try:
            with open(fpath, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
        except Exception:
            return ""
        return h.hexdigest()
