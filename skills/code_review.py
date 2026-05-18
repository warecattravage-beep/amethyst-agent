"""
✦ Code Review Skill — Read a file and return it for the model to review.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from core.skill import Skill

log = logging.getLogger("onyx.skill.code_review")


class CodeReviewSkill(Skill):
    """Review code by reading a file and returning it for AI analysis."""

    def __init__(self, config: dict):
        super().__init__("code_review", config)

    async def run(self, context: dict[str, Any], **kwargs) -> str:
        """Read a code file and return it with a review prompt.

        Args:
            path: Path to the file to review

        Returns:
            File contents wrapped in a review request prefix.
        """
        path_str = kwargs.get("path", "").strip()
        if not path_str:
            return "Error: No path provided."

        file_path = Path(path_str).expanduser()

        try:
            if not file_path.exists():
                return f"Error: File not found: {file_path}"
            if not file_path.is_file():
                return f"Error: Not a file: {file_path}"

            content = file_path.read_text(encoding="utf-8", errors="replace")
            max_len = 12000
            if len(content) > max_len:
                content = content[:max_len] + "\n\n[... truncated at {max_len} characters]"

            return (
                f"Review this code:\n\n"
                f"File: {file_path}\n"
                f"```\n{content}\n```\n\n"
                f"Please review this code for potential bugs, security issues, "
                f"performance improvements, and code style concerns."
            )
        except PermissionError:
            return f"Error: Permission denied: {file_path}"
        except Exception as e:
            return f"Error reading file: {e}"
