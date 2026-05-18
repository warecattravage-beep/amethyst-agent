"""
✦ File Skill — Read and write files.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from core.skill import Skill

log = logging.getLogger("onyx.skill.file")

# Allowed base directories for file operations
ALLOWED_PATHS = [
    Path.home() / "Projects",
    Path.home(),
    Path("/tmp"),
]


def _is_safe(path: Path) -> bool:
    """Check if path is within allowed directories."""
    resolved = path.resolve()
    for allowed in ALLOWED_PATHS:
        try:
            resolved.relative_to(allowed.resolve())
            return True
        except ValueError:
            continue
    return False


class FileSkill(Skill):
    """Read and write files on the local filesystem."""

    def __init__(self, config: dict):
        super().__init__("file", config)

    async def run(self, context: dict[str, Any], **kwargs) -> str:
        """Read or write a file.

        Args:
            path: Path to the file (required)
            content: Content to write (if provided, writes; otherwise reads)

        Returns:
            File contents (read) or success/failure message (write).
        """
        path_str = kwargs.get("path", "").strip()
        if not path_str:
            return "Error: No path provided."

        file_path = Path(path_str).expanduser()

        if not _is_safe(file_path):
            return (
                f"Error: Path '{path_str}' is not allowed. "
                f"Allowed paths: ~/Projects/, ~/, /tmp/"
            )

        content = kwargs.get("content")

        if content is not None:
            # Write mode
            return await self._write_file(file_path, str(content))
        else:
            # Read mode
            return await self._read_file(file_path)

    async def _read_file(self, path: Path) -> str:
        """Read and return file contents."""
        try:
            if not path.exists():
                return f"Error: File not found: {path}"
            if not path.is_file():
                return f"Error: Not a file: {path}"

            content = path.read_text(encoding="utf-8", errors="replace")
            if len(content) > 8000:
                content = content[:8000] + "\n\n[... truncated at 8000 characters]"
            return content
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except Exception as e:
            return f"Error reading file: {e}"

    async def _write_file(self, path: Path, content: str) -> str:
        """Write content to file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"✅ Written {len(content)} bytes to {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except Exception as e:
            return f"Error writing file: {e}"
