"""Memory subsystem - short-term (conversation) + long-term (file-based)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import config


class ConversationMemory:
    """Rolling short-term memory of recent conversation turns."""

    def __init__(self, max_turns: int | None = None):
        self.max_turns = max_turns or config.max_history
        self.turns: list[dict] = []  # {"role": "assistant"|"user", "content": str}
        self._tool_results: list[tuple[str, str]] = []  # (tool_name, result)

    def add_user(self, msg: str):
        self.turns.append({"role": "user", "content": msg})
        self._trim()

    def add_assistant(self, msg: str):
        self.turns.append({"role": "assistant", "content": msg})
        self._trim()

    def add_tool_result(self, tool_name: str, result: str):
        """Store tool call result for context."""
        self._tool_results.append((tool_name, result))
        if len(self._tool_results) > 10:
            self._tool_results.pop(0)

    def to_ollama_format(self) -> list[dict]:
        """Convert to Ollama-compatible message list."""
        return list(self.turns)

    def _trim(self):
        while len(self.turns) > self.max_turns * 2:
            self.turns.pop(0)

    def clear(self):
        self.turns.clear()
        self._tool_results.clear()


class LongTermMemory:
    """File-based persistent long-term memory."""

    def __init__(self, base_dir: str | Path = "memory"):
        self.base = Path(base_dir) / "long_term"
        self.base.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, content: str):
        path = self.base / f"{key}.md"
        path.write_text(content)
        return str(path)

    def read(self, key: str) -> Optional[str]:
        path = self.base / f"{key}.md"
        if path.exists():
            return path.read_text()
        return None

    def list_keys(self) -> list[str]:
        return sorted(p.stem for p in self.base.glob("*.md"))

    def delete(self, key: str):
        path = self.base / f"{key}.md"
        if path.exists():
            path.unlink()


def log_conversation(turns: list[dict]):
    """Append a conversation log to today's log file."""
    if not config.log_file:
        return
    path = Path(config.log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    entry = {"timestamp": ts, "turns": turns}
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
