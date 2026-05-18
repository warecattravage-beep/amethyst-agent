"""
✦ Console Messenger — Local terminal interface.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from core.messenger import Messenger

log = logging.getLogger("onyx.console")


class ConsoleMessenger(Messenger):
    """Local terminal chat interface using rich (lazy import)."""

    def __init__(self, config: dict):
        super().__init__("console", config)
        self.rich = None
        self.prompt = config.get("prompt", "onyx> ")

    def _get_rich(self):
        """Lazy-load rich to avoid import failures on machines without it."""
        if self.rich is None:
            from rich.console import Console as RichConsole
            from rich.markdown import Markdown
            from rich.panel import Panel
            self._RichConsole = RichConsole
            self._Markdown = Markdown
            self._Panel = Panel
            self.rich = RichConsole()
        return self.rich

    async def start(self):
        rich = self._get_rich()
        self._running = True
        rich.print(self._Panel(
            "✦ Onyx Agent — Console Mode\n"
            "Type your messages. /help for commands, /quit to exit.",
            title="Onyx",
            border_style="cyan",
        ))
        log.info("Console messenger started")

    async def stop(self):
        self._running = False
        if self.rich:
            self.rich.print("\n[yellow]Goodbye![/]")
        log.info("Console messenger stopped")

    async def send(self, target: str, text: str, **kwargs):
        """Display AI response in the console."""
        rich = self._get_rich()
        rich.print()
        rich.print(self._Panel(
            self._Markdown(text),
            title="Onyx",
            border_style="green",
        ))
        rich.print()

    async def read_input(self) -> str | None:
        """Read a single line of input."""
        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, input, f"\n{self.prompt}")
            return text.strip()
        except (EOFError, KeyboardInterrupt):
            return None

    def print_status(self, items: list[tuple[str, str]]):
        """Print a status table."""
        if not self.rich:
            return
        self.rich.print()
        for label, value in items:
            self.rich.print(f"  [cyan]{label}:[/] {value}")
        self.rich.print()
