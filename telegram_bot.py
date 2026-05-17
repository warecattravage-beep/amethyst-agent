#!/usr/bin/env python3
"""Onyx Agent — Telegram bot interface.

Run:  python telegram_bot.py <BOT_TOKEN>

Get a bot token from @BotFather on Telegram.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent import Agent
from config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("onyx.telegram")


class TelegramBot:
    """Minimal Telegram bot using the HTTP API directly (no external lib needed)."""

    def __init__(self, token: str):
        self.token = token
        self.api_base = f"https://api.telegram.org/bot{token}"
        self.agent = Agent()
        self.offset = 0
        self._running = True

    async def _api(self, method: str, **kwargs):
        """Call Telegram Bot API."""
        import httpx
        url = f"{self.api_base}/{method}"
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(url, json=kwargs, timeout=30)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                logger.error("Telegram API error (%s): %s", method, e)
                return {"ok": False}

    async def send_message(self, chat_id: int, text: str):
        await self._api("sendMessage", chat_id=chat_id, text=text)

    async def send_typing(self, chat_id: int):
        await self._api("sendChatAction", chat_id=chat_id, action="typing")

    async def handle_update(self, update: dict):
        """Process a single Telegram update."""
        msg = update.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip()

        if not chat_id or not text:
            return

        # Ignore commands meant for OpenClaw
        if text.startswith("/"):
            if text == "/start":
                await self.send_message(chat_id,
                    "✦ Onyx Agent\n\n"
                    "Gemma 4 E4B running locally on your tablet.\n"
                    "Send me a message and I'll think + act.\n"
                    "Commands: /reset, /tools, /model <name>, /help")
                return
            elif text == "/reset":
                await self.agent.reset()
                await self.send_message(chat_id, "Conversation reset.")
                return
            elif text == "/tools":
                from tools import TOOL_REGISTRY
                reply = "Tools:\n" + "\n".join(f"• {n}" for n in TOOL_REGISTRY)
                await self.send_message(chat_id, reply)
                return
            elif text.startswith("/model "):
                config.model = text[7:].strip()
                await self.send_message(chat_id, f"Model set to: {config.model}")
                return
            elif text == "/help":
                await self.send_message(chat_id,
                    "/reset — Clear history\n"
                    "/tools — List tools\n"
                    "/model <name> — Switch model\n"
                    "/help — This")
                return
            else:
                return

        # Handle the actual message
        await self.send_typing(chat_id)
        try:
            reply = await self.agent.chat(text, stream=False)
            # Telegram has a 4096 char limit per message
            if len(reply) > 4000:
                parts = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
                for part in parts:
                    await self.send_message(chat_id, part)
                    await asyncio.sleep(0.3)
            else:
                await self.send_message(chat_id, reply)
        except Exception as e:
            logger.exception("Error processing message")
            await self.send_message(chat_id, f"Error: {e}")

    async def poll_loop(self):
        """Long-poll for updates."""
        logger.info("Telegram bot started — polling for updates...")
        while self._running:
            try:
                result = await self._api(
                    "getUpdates",
                    offset=self.offset,
                    timeout=30,
                    allowed_updates=["message"],
                )
                if result.get("ok"):
                    for update in result.get("result", []):
                        self.offset = update["update_id"] + 1
                        await self.handle_update(update)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Poll error: %s", e)
                await asyncio.sleep(5)

    def run(self):
        try:
            asyncio.run(self.poll_loop())
        except KeyboardInterrupt:
            self._running = False
            logger.info("Shutting down.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python telegram_bot.py <BOT_TOKEN>")
        print("Get a token from @BotFather on Telegram.")
        sys.exit(1)

    token = sys.argv[1]
    bot = TelegramBot(token)
    bot.run()


if __name__ == "__main__":
    main()
