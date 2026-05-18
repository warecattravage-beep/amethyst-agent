"""
✦ Project Skill - Create, read, and list multi-file projects.
All file operations are confined to ~/Projects/ for safety.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from core.skill import Skill

log = logging.getLogger("onyx.skill.project")

PROJECTS_DIR = Path.home() / "Projects"


def _validate_project_path(path: str) -> Path | None:
    """Resolve and validate a path is under ~/Projects/. Returns None if unsafe."""
    resolved = Path(path).expanduser().resolve()
    try:
        resolved.relative_to(PROJECTS_DIR)
        return resolved
    except ValueError:
        return None


class ProjectSkill(Skill):
    """Create and manage project files under ~/Projects/."""

    def __init__(self, config: dict):
        super().__init__("project", config)

    async def run(self, context: dict[str, Any], **kwargs) -> str:
        """Manage project files.

        Args:
            action: 'create', 'read', or 'list'
            path: Project directory or file path (relative to ~/Projects/)
            content: Content for file operations (optional)
            files: Dict of relative_file_path -> content for bulk create

        Returns:
            Result string describing what was done.
        """
        action = kwargs.get("action", "").strip().lower()
        if not action:
            return "Error: No action specified. Use create, read, or list."

        if action == "create":
            return await self._create(kwargs)
        elif action == "read":
            return await self._read(kwargs)
        elif action == "list":
            return await self._list(kwargs)
        else:
            return f"Error: Unknown action '{action}'. Use create, read, or list."

    async def _create(self, kwargs: dict) -> str:
        """Create files in a project."""
        files = kwargs.get("files")
        if not files or not isinstance(files, dict):
            return "Error: 'files' must be a dict of path -> content."

        project_path_str = kwargs.get("path", "").strip()
        if not project_path_str:
            return "Error: No project path specified."

        # Validate project dir
        project_dir = _validate_project_path(project_path_str)
        if project_dir is None:
            return f"Error: Path '{project_path_str}' is outside ~/Projects/."

        created = []
        for rel_path, content in files.items():
            full_path = project_dir / rel_path
            # Validate each file is still inside the project dir
            try:
                full_path.resolve().relative_to(PROJECTS_DIR)
            except ValueError:
                created.append(f"⛔ {rel_path} - skipped (outside ~/Projects/)")
                continue

            try:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(str(content), encoding="utf-8")
                created.append(f"✅ {rel_path} ({len(str(content))} bytes)")
            except Exception as e:
                created.append(f"❌ {rel_path} - {e}")

        if not created:
            return "No files created."

        lines = [
            f"**Project created in {project_dir.relative_to(PROJECTS_DIR)}**",
            "",
            *created,
        ]
        return "\n".join(lines)

    async def _read(self, kwargs: dict) -> str:
        """Read a file from a project."""
        path_str = kwargs.get("path", "").strip()
        if not path_str:
            return "Error: No path specified."

        file_path = _validate_project_path(path_str)
        if file_path is None:
            return f"Error: Path '{path_str}' is outside ~/Projects/."

        if not file_path.exists():
            return f"Error: File not found: {file_path.relative_to(PROJECTS_DIR)}"
        if not file_path.is_file():
            return f"Error: Not a file: {file_path.relative_to(PROJECTS_DIR)}"

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if len(content) > 8000:
                content = content[:8000] + "\n\n[... truncated at 8000 characters]"
            rel = file_path.relative_to(PROJECTS_DIR)
            return f"**{rel}** ({len(content)} bytes)\n\n```\n{content}\n```"
        except Exception as e:
            return f"Error reading file: {e}"

    async def _list(self, kwargs: dict) -> str:
        """List files in a project directory."""
        path_str = kwargs.get("path", "").strip()
        if not path_str:
            return "Error: No path specified."

        dir_path = _validate_project_path(path_str)
        if dir_path is None:
            return f"Error: Path '{path_str}' is outside ~/Projects/."

        if not dir_path.exists():
            return f"Error: Directory not found: {dir_path.relative_to(PROJECTS_DIR)}"
        if not dir_path.is_dir():
            return f"Error: Not a directory: {dir_path.relative_to(PROJECTS_DIR)}"

        try:
            files = []
            dirs = []
            for entry in sorted(dir_path.iterdir()):
                rel = entry.relative_to(PROJECTS_DIR)
                if entry.is_dir():
                    dirs.append(f"  📁 {rel}/")
                else:
                    size = entry.stat().st_size
                    files.append(f"  📄 {rel} ({size:,} bytes)")

            rel = dir_path.relative_to(PROJECTS_DIR)
            lines = [f"**{rel}/**"]
            if dirs:
                lines.append("")
                lines.extend(dirs)
            if files:
                lines.append("")
                lines.extend(files)
            if not dirs and not files:
                lines.append("\n_(empty directory)_")

            return "\n".join(lines)
        except Exception as e:
            return f"Error listing directory: {e}"
