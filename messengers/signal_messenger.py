"""
✦ Signal Messenger - CLI-based Signal interface.
Uses signal-cli for sending and receiving messages via subprocess.
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
from typing import Any

from core.messenger import Messenger

log = logging.getLogger("onyx.signal")


class SignalMessenger(Messenger):
    """Signal messenger using signal-cli CLI."""

    def __init__(self, config: dict):
        super().__init__("signal", config)
        self.account = config.get("account", "")
        self.cli_path = shutil.which(config.get("cli_path", "signal-cli")) or config.get("cli_path", "signal-cli")
        self._available = False

    async def start(self):
        if not self.account:
            log.warning("Signal: no account configured")
            return
        if not shutil.which(self.cli_path):
            log.warning("Signal: signal-cli not found at '%s'", self.cli_path)
            return
        self._available = True
        self._running = True
        log.info("Signal messenger ready - account: %s", self.account)

    async def stop(self):
        self._running = False

    async def _run_cli(self, *args: str) -> tuple[str, str]:
        """Run signal-cli with given arguments."""
        cmd = [self.cli_path] + list(args)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            return stdout.decode().strip(), stderr.decode().strip()
        except asyncio.TimeoutError:
            log.warning("Signal CLI timed out")
            return "", "timeout"
        except FileNotFoundError:
            self._available = False
            return "", "signal-cli not found"
        except Exception as e:
            log.warning("Signal CLI error: %s", e)
            return "", str(e)

    async def send(self, target: str, text: str, **kwargs):
        """Send a message via signal-cli."""
        if not self._available or not self._running:
            log.debug("Signal: not available, dropping message")
            return
        stdout, stderr = await self._run_cli(
            "send",
            "-u", self.account,
            "-m", text,
            target,
        )
        if stderr and "timeout" not in stderr:
            log.warning("Signal send error to %s: %s", target, stderr[:200])

    async def poll(self):
        """Poll for incoming messages via signal-cli receive."""
        if not self._available or not self._running:
            return
        stdout, stderr = await self._run_cli(
            "receive",
            "-u", self.account,
            "--json",
        )
        if not stdout:
            return

        try:
            messages = json.loads(stdout)
            if not isinstance(messages, list):
                messages = [messages]
        except json.JSONDecodeError:
            log.debug("Signal: could not parse receive output")
            return

        for msg in messages:
            envelope = msg.get("envelope", {})
            data_message = envelope.get("dataMessage", {})
            sync_message = envelope.get("syncMessage", {})

            # Get text from data message or sync message (sent from this device)
            text = data_message.get("message", "")
            if not text:
                text = sync_message.get("sentMessage", {}).get("message", "")

            if not text:
                continue

            source = envelope.get("sourceNumber", envelope.get("sourceUuid", ""))
            if not source:
                continue

            target_number = data_message.get("destination", "")

            await self._handle(text.strip(), {
                "source": "signal",
                "chat_id": source,
                "sender": source,
                "message_id": data_message.get("timestamp", ""),
                "destination": target_number,
            })
