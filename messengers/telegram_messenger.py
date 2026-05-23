"""
✦ Telegram Messenger - Bot interface.
"""
from __future__ import annotations

import base64
import logging
from typing import Any
from pathlib import Path

from core.messenger import Messenger

log = logging.getLogger("amethyst.telegram")


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
        import httpx
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

    async def send_action(self, target: str, action: str = "typing"):
        """Send a chat action (typing indicator)."""
        if not self._running:
            return
        await self._api(
            "sendChatAction",
            chat_id=int(target),
            action=action,
        )

    async def _download_file(self, file_id: str) -> bytes | None:
        """Download a file from Telegram by file_id, return raw bytes."""
        if not self._http:
            return None
        try:
            # Get file path from Telegram
            result = await self._api("getFile", file_id=file_id)
            if not result or "file_path" not in result:
                return None
            file_path = result["file_path"]
            url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            r = await self._http.get(url, timeout=30)
            if r.status_code == 200:
                return r.content
        except Exception as e:
            log.debug("Telegram file download error: %s", e)
        return None

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
            if not chat_id:
                continue

            text = (msg.get("text") or "").strip()
            images = []

            # Check for photo messages
            if "photo" in msg:
                # Pick the largest photo (last in array)
                largest = msg["photo"][-1]
                file_bytes = await self._download_file(largest["file_id"])
                if file_bytes:
                    b64 = base64.b64encode(file_bytes).decode("utf-8")
                    images.append(b64)
                    if not text:
                        text = "What's in this image?"

            # Check for document messages (especially images)
            if "document" in msg:
                doc = msg["document"]
                mime = (doc.get("mime_type") or "").lower()
                if mime.startswith("image/"):
                    file_bytes = await self._download_file(doc["file_id"])
                    if file_bytes:
                        b64 = base64.b64encode(file_bytes).decode("utf-8")
                        images.append(b64)
                        if not text:
                            text = f"What's in this {'photo' if mime == 'image/png' else 'image'}?"

            if chat_id and (text or images):
                meta = {
                    "source": "telegram",
                    "chat_id": str(chat_id),
                    "sender": msg.get("from", {}).get("first_name", "?"),
                    "message_id": msg.get("message_id"),
                }
                if images:
                    meta["images"] = images
                await self._handle(text, meta)
