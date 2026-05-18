"""
✦ Terminal Skill — Execute shell commands.
"""
from __future__ import annotations

import logging
import subprocess
from typing import Any

from core.skill import Skill

log = logging.getLogger("onyx.skill.terminal")

# Commands that are always blocked for safety
BLOCKED_PREFIXES = [
    "sudo", "su ", "passwd", "rm -rf /", "dd if=", "mkfs", "shutdown",
    "reboot", "poweroff", "init ",
]
BLOCKED_WORDS = ["rm -rf --no-preserve-root"]


class TerminalSkill(Skill):
    """Run shell commands and return output."""

    def __init__(self, config: dict):
        super().__init__("terminal", config)

    def _is_safe(self, cmd: str) -> tuple[bool, str]:
        """Check if a command is safe to run."""
        lower = cmd.lower().strip()
        for prefix in BLOCKED_PREFIXES:
            if lower.startswith(prefix):
                return False, f"Command blocked: starts with '{prefix}'"
        for word in BLOCKED_WORDS:
            if word in lower:
                return False, f"Command blocked: contains '{word}'"
        return True, ""

    async def run(self, context: dict[str, Any], **kwargs) -> str:
        """Run a shell command."""
        cmd = kwargs.get("command", "")
        timeout = kwargs.get("timeout", 15)

        if not cmd:
            return "No command provided."

        safe, reason = self._is_safe(cmd)
        if not safe:
            return f"Safety check failed: {reason}"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = []
            if result.stdout:
                output.append(f"```\n{result.stdout.strip()[:2000]}\n```")
            if result.stderr:
                output.append(f"**Stderr:**\n```\n{result.stderr.strip()[:1000]}\n```")
            if result.returncode != 0:
                output.append(f"Exit code: {result.returncode}")

            return "\n".join(output) if output else "(no output)"

        except subprocess.TimeoutExpired:
            return f"Error: command timed out ({timeout}s limit)"
        except Exception as e:
            return f"Error: {e}"
