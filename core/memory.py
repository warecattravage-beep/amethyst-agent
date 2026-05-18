"""
✦ Onyx Memory — Conversation history manager.
Stores per-chat message history and trims to keep context size manageable.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("onyx.memory")

MAX_HISTORY = 20  # max messages to keep per chat
MAX_AGE = 86400 * 7  # 7 days


class Memory:
    """Persistent conversation memory per chat."""

    def __init__(self, path: str | Path = "data/memory.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, list[dict]] = {}
        self._dirty = False
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except Exception as e:
                log.warning("Memory load error: %s", e)
                self.data = {}

    def save(self):
        if not self._dirty:
            return
        try:
            self.path.write_text(json.dumps(self.data, indent=2))
            self._dirty = False
        except Exception as e:
            log.warning("Memory save error: %s", e)

    def add(self, chat_id: str, role: str, content: str):
        """Add a message to chat history."""
        self.data.setdefault(chat_id, [])
        self.data[chat_id].append({
            "role": role,
            "content": content,
            "ts": time.time(),
        })
        self._trim(chat_id)
        self._dirty = True

    def get_context(self, chat_id: str, max_msgs: int = 10) -> list[dict]:
        """Get recent messages for model context."""
        history = self.data.get(chat_id, [])
        # Return last N messages, oldest first
        recent = history[-max_msgs:]
        return [{"role": m["role"], "content": m["content"]} for m in recent]

    def _trim(self, chat_id: str):
        """Trim old messages beyond limits."""
        msgs = self.data.get(chat_id, [])
        now = time.time()
        # Remove expired
        msgs = [m for m in msgs if now - m.get("ts", 0) < MAX_AGE]
        # Keep only last N
        if len(msgs) > MAX_HISTORY:
            msgs = msgs[-MAX_HISTORY:]
        self.data[chat_id] = msgs

    def clear(self, chat_id: str):
        """Clear history for a chat."""
        self.data.pop(chat_id, None)
        self._dirty = True
