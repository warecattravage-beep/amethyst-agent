"""
✦ Console Messenger — Local terminal interface.
Falls back to plain print/input when rich is not installed (e.g. Termux).
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from core.messenger import Messenger

log = logging.getLogger("onyx.console")


class ConsoleMessenger(Messenger):
    """Local terminal chat interface. Uses rich if available, falls back to plain I/O."""

    def __init__(self, config: dict):
        super().__init__("console", config)
        self.rich = None
        self.use_rich = False
        self.prompt = config.get("prompt", "onyx> ")

    def _try_rich(self):
        """Try to load rich. Returns True if successful."""
        if self.rich is not None:
            return self.use_rich
        try:
            from rich.console import Console as RichConsole
            from rich.markdown import Markdown
            from rich.panel import Panel
            self._RichConsole = RichConsole
            self._Markdown = Markdown
            self._Panel = Panel
            self.rich = RichConsole()
            self.use_rich = True
        except ImportError:
            self.use_rich = False
            log.info("rich not available — console using plain I/O")
        return self.use_rich

    async def start(self):
        self._running = True
        if self._try_rich():
            self.rich.print(self._Panel(
                "✦ Onyx Agent — Console Mode\n"
                "Type your messages. /help for commands, /quit to exit.",
                title="Onyx",
                border_style="cyan",
            ))
        else:
            print("\n✦ Onyx Agent — Console Mode")
            print("Type your messages. /help for commands, /quit to exit.")
        log.info("Console messenger started")

    async def stop(self):
        self._running = False
        if self.rich:
            self.rich.print("\n[yellow]Goodbye![/]")
        else:
            print("\nGoodbye!")
        log.info("Console messenger stopped")

    async def send(self, target: str, text: str, **kwargs):
        """Display AI response in the console."""
        if self._try_rich():
            self.rich.print()
            self.rich.print(self._Panel(
                self._Markdown(text),
                title="Onyx",
                border_style="green",
            ))
            self.rich.print()
        else:
            print(f"\n─── Onyx ───\n{text}\n────────────\n")

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
        if self._try_rich():
            self.rich.print()
            for label, value in items:
                self.rich.print(f"  [cyan]{label}:[/] {value}")
            self.rich.print()
        else:
            print()
            for label, value in items:
                print(f"  {label}: {value}")
            print()
