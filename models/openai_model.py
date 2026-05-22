"""
✦ OpenAI Model - API-based models (OpenAI, OpenRouter, etc.).
"""
from __future__ import annotations

import logging
from typing import Any

from core.model import Model

log = logging.getLogger("amethyst.openai")


class OpenAIModel(Model):
    """OpenAI-compatible API models."""

    def __init__(self, config: dict):
        super().__init__("openai", config)
        self.api_key = config.get("api_key", "")
        self.model_name = config.get("model", "gpt-4o")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self._client: AsyncOpenAI | None = None

    async def start(self):
        from openai import AsyncOpenAI
        if not self.api_key:
            log.warning("OpenAI: no API key configured")
            return
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        ok = await self.check()
        if ok:
            log.info("OpenAI: %s", self.model_name)

    async def stop(self):
        if self._client:
            await self._client.close()

    async def check(self) -> bool:
        if not self._client:
            return False
        try:
            models = await self._client.models.list()
            return any(m.id == self.model_name for m in models)
        except Exception:
            # Models list might not be available; assume it works
            return True

    async def chat(self, messages: list[dict], **kwargs) -> str:
        if not self._client:
            return "Error: OpenAI not configured."
        try:
            r = await self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            return r.choices[0].message.content or ""
        except Exception as e:
            log.error("OpenAI chat error: %s", e)
            return f"Error: {e}"
