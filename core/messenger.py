"""
✦ Amethyst Messenger Base - Interface for all messengers.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Callable, Any

log = logging.getLogger("amethyst.messenger")

MessageHandler = Callable[[str, dict[str, Any]], None]


class Messenger(ABC):
    """Base class for all messenger integrations."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self._handler: MessageHandler | None = None
        self._running = False

    def on_message(self, handler: MessageHandler):
        """Register the message handler callback."""
        self._handler = handler

    @abstractmethod
    async def start(self):
        """Start the messenger client."""
        ...

    @abstractmethod
    async def stop(self):
        """Stop the messenger client."""
        ...

    @abstractmethod
    async def send(self, target: str, text: str, **kwargs):
        """Send a message to a target (chat/channel/user)."""
        ...

    async def _handle(self, text: str, meta: dict[str, Any]):
        """Internal handler - calls registered handler."""
        if self._handler:
            try:
                await self._handler(text, meta)
            except Exception as e:
                log.error("Handler error on %s: %s", self.name, e)

    @property
    def is_running(self) -> bool:
        return self._running
