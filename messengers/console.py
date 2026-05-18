"""
✦ Console Messenger — Local terminal interface.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from rich.console import Console as RichConsole
from rich.markdown import Markdown
from rich.panel import Panel

from core.messenger import Messenger

log = logging.getLogger("onyx.console")


class ConsoleMessenger(Messenger):
    """Local terminal chat interface using rich."""

    def __init__(self, config: dict):
        super().__init__("console", config)
        self.rich = RichConsole()
        self.prompt = config.get("prompt", "onyx> ")

    async def start(self):
        self._running = True
        self.rich.print(Panel(
            "✦ Onyx Agent — Console Mode\n"
            "Type your messages. /help for commands, /quit to exit.",
            title="Onyx",
            border_style="cyan",
        ))
        log.info("Console messenger started")

    async def stop(self):
        self._running = False
        self.rich.print("\n[yellow]Goodbye![/]")
        log.info("Console messenger stopped")

    async def send(self, target: str, text: str, **kwargs):
        """Display AI response in the console."""
        self.rich.print()
        self.rich.print(Panel(
            Markdown(text),
            title="Onyx",
            border_style="green",
        ))
        self.rich.print()

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
        self.rich.print()
        for label, value in items:
            self.rich.print(f"  [cyan]{label}:[/] {value}")
        self.rich.print()
