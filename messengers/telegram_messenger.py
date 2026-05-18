"""
✦ Telegram Messenger — Bot interface.
"""
from __future__ import annotations

import logging
from typing import Any
from pathlib import Path

from core.messenger import Messenger

log = logging.getLogger("onyx.telegram")


class TelegramMessenger(Messenger):
    """Telegram bot messenger using raw HTTP API (no polling conflicts)."""

    def __init__(self, config: dict):
        super().__init__("telegram", config)
        self.token = config.get("token", "")
        self._base = f"https://api.telegram.org/bot{self.token}" if self.token else ""
        self._offset = 0
        self._me = None
        self._http: httpx.AsyncClient | None = None

    async def _api(self, method: str, **kwargs) -> dict | None:
        """Call Telegram API."""
        if not self._http:
            return None
        try:
            r = await self._http.post(
                f"{self._base}/{method}",
                json=kwargs,
                timeout=15,
            )
            data = r.json()
            if data.get("ok"):
                return data.get("result")
            log.warning("Telegram API error: %s", data.get("description", "?"))
        except httpx.ConnectError:
            log.debug("Telegram: connection refused (offline?)")
        except httpx.TimeoutException:
            log.debug("Telegram: request timed out")
        except Exception as e:
            log.debug("Telegram API error: %s", e)
        return None

    async def start(self):
        if not self.token:
            log.warning("Telegram: no token configured")
            return
        import httpx

        # Try with SSL verification first
        self._http = httpx.AsyncClient(verify=True)
        self._me = await self._api("getMe")

        # Fallback: no SSL cert verification (Termux)
        if not self._me:
            await self._http.aclose()
            self._http = httpx.AsyncClient(verify=False)
            self._me = await self._api("getMe")
            if self._me:
                log.info("Telegram: connected with SSL verify=False")

        if self._me:
            log.info("Telegram bot: @%s", self._me.get("username", "?"))
            self._running = True
        else:
            log.warning("Telegram: could not reach API (offline/invalid token/SSL)")

    async def stop(self):
        self._running = False
        if self._http:
            await self._http.aclose()

    async def send(self, target: str, text: str, **kwargs):
        """Send message to a Telegram chat."""
        if not self._running:
            return
        await self._api(
            "sendMessage",
            chat_id=int(target),
            text=text,
            parse_mode=kwargs.get("parse_mode", "Markdown"),
            disable_notification=kwargs.get("silent", False),
        )

    async def poll(self):
        """Long-poll for incoming messages."""
        if not self._running:
            return
        result = await self._api(
            "getUpdates",
            offset=self._offset,
            timeout=30,
            allowed_updates=["message"],
        )
        if not result:
            return
        for update in result:
            self._offset = update["update_id"] + 1
            msg = update.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            text = (msg.get("text") or "").strip()
            if chat_id and text:
                await self._handle(text, {
                    "source": "telegram",
                    "chat_id": str(chat_id),
                    "sender": msg.get("from", {}).get("first_name", "?"),
                    "message_id": msg.get("message_id"),
                })
