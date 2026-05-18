"""
✦ Coding Skill - Write, review, and execute code.
"""
from __future__ import annotations

import ast
import logging
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from core.skill import Skill

log = logging.getLogger("onyx.skill.coding")


class CodingSkill(Skill):
    """Write, analyze, and execute code in Python (and other languages)."""

    def __init__(self, config: dict):
        super().__init__("coding", config)
        self.allowed_languages = {"py": "python3", "sh": "bash", "js": "node"}

    async def run(self, context: dict[str, Any], **kwargs) -> str:
        """Execute a code block. Expects kwargs['code'] and kwargs['language']."""
        code = kwargs.get("code", "")
        language = kwargs.get("language", "py")

        if not code:
            return "No code provided."

        ext = language.lower().strip().lstrip(".")
        interpreter = self.allowed_languages.get(ext)

        if not interpreter:
            return f"Unsupported language: {language}. Supported: {', '.join(self.allowed_languages.keys())}"

        # Safety check for Python
        if ext == "py":
            try:
                ast.parse(code)
            except SyntaxError as e:
                return f"Syntax error: {e}"

        # Execute in temporary file
        try:
            suffix = f".{ext}"
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=suffix, delete=False, dir="/tmp"
            ) as f:
                f.write(code)
                tmp_path = f.name

            result = subprocess.run(
                [interpreter, tmp_path],
                capture_output=True, text=True, timeout=30,
                cwd="/tmp",
            )

            Path(tmp_path).unlink(missing_ok=True)

            output = []
            if result.stdout:
                output.append(f"**Output:**\n```\n{result.stdout.strip()}\n```")
            if result.stderr:
                output.append(f"**Stderr:**\n```\n{result.stderr.strip()}\n```")
            if result.returncode != 0:
                output.append(f"**Exit code:** {result.returncode}")

            return "\n".join(output) if output else "(no output)"

        except subprocess.TimeoutExpired:
            Path(tmp_path).unlink(missing_ok=True)
            return "Error: execution timed out (30s limit)"
        except Exception as e:
            return f"Error: {e}"
