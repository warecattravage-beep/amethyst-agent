"""
✦ Discord Messenger - Bot with gateway (real-time messages).
Uses discord.py client for both sending and receiving.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.messenger import Messenger

log = logging.getLogger("amethyst.discord")


class DiscordMessenger(Messenger):
    """Discord bot with full gateway support via discord.py."""

    def __init__(self, config: dict):
        super().__init__("discord", config)
        self.token = config.get("token", "")
        self._client = None
        self._ready = asyncio.Event()

    async def start(self):
        if not self.token:
            log.warning("Discord: no token configured")
            return
        try:
            import discord
            intents = discord.Intents.default()
            intents.message_content = True

            class AmethystBot(discord.Client):
                def __init__(self, messenger):
                    super().__init__(intents=intents)
                    self.messenger = messenger

                async def on_ready(self):
                    log.info("Discord bot: @%s (%d guilds)",
                             self.user.name, len(self.guilds))
                    self.messenger._ready.set()
                    self.messenger._running = True

                async def on_message(self, msg):
                    if msg.author == self.user:
                        return
                    text = msg.content.strip()
                    if not text:
                        return
                    await self.messenger._handle(text, {
                        "source": "discord",
                        "chat_id": str(msg.channel.id),
                        "channel": str(msg.channel.name),
                        "sender": str(msg.author),
                        "author_id": str(msg.author.id),
                        "guild": str(msg.guild.name) if msg.guild else "DM",
                        "message_id": msg.id,
                    })

            self._client = AmethystBot(self)
            asyncio.create_task(self._client.start(self.token))
            # Wait for ready
            try:
                await asyncio.wait_for(self._ready.wait(), timeout=15)
            except asyncio.TimeoutError:
                log.warning("Discord: connection timed out")

        except ImportError:
            log.warning("Discord: discord.py not installed. pip install discord.py")

    async def stop(self):
        self._running = False
        if self._client:
            await self._client.close()

    async def send(self, target: str, text: str, **kwargs):
        """Send message to a Discord channel."""
        if not self._client or not self._client.is_ready():
            return
        try:
            channel = self._client.get_channel(int(target))
            if channel:
                await channel.send(text[:2000])
        except Exception as e:
            log.error("Discord send failed: %s", e)
