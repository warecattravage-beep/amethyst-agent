"""
✦ Discord Messenger — Bot interface.
"""
from __future__ import annotations

import logging
from typing import Any

from core.messenger import Messenger

log = logging.getLogger("onyx.discord")


class DiscordMessenger(Messenger):
    """Discord bot messenger using HTTP API (no gateway)."""

    def __init__(self, config: dict):
        super().__init__("discord", config)
        self.token = config.get("token", "")
        self._base = "https://discord.com/api/v10"
        self._http: httpx.AsyncClient | None = None

    def _headers(self):
        return {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }

    async def start(self):
        import httpx
        if not self.token:
            log.warning("Discord: no token configured")
            return
        self._http = httpx.AsyncClient()
        # Verify bot token
        r = await self._http.get(f"{self._base}/users/@me", headers=self._headers())
        if r.status_code == 200:
            data = r.json()
            log.info("Discord bot: @%s", data.get("username", "?"))
            self._running = True
        else:
            log.warning("Discord: invalid token (HTTP %d)", r.status_code)

    async def stop(self):
        self._running = False
        if self._http:
            await self._http.aclose()

    async def send(self, target: str, text: str, **kwargs):
        """Send message to a Discord channel (target = channel_id)."""
        if not self._http:
            return
        try:
            await self._http.post(
                f"{self._base}/channels/{target}/messages",
                headers=self._headers(),
                json={"content": text},
                timeout=15,
            )
        except Exception as e:
            log.error("Discord send failed: %s", e)

    async def poll(self):
        """Poll for new messages via getChannelMessages."""
        # Discord HTTP API doesn't support polling easily without gateway.
        # For v1, this messenger requires webhook or gateway setup.
        # Placeholder for future implementation.
        pass
