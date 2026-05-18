"""
✦ Ollama Model — Local LLM via Ollama.
"""
from __future__ import annotations

import logging
from typing import Any

from core.model import Model

log = logging.getLogger("onyx.ollama")


class OllamaModel(Model):
    """Local models via Ollama API."""

    def __init__(self, config: dict):
        super().__init__("ollama", config)
        self.host = config.get("host", "http://localhost:11434")
        self.model = config.get("model", "gemma2:9b")
        self.timeout = config.get("timeout", 60)
        self._http: httpx.AsyncClient | None = None

    async def start(self):
        import httpx
        self._http = httpx.AsyncClient(timeout=self.timeout)
        ok = await self.check()
        if ok:
            log.info("Ollama: %s at %s", self.model, self.host)
        else:
            log.warning("Ollama: not reachable at %s", self.host)

    async def stop(self):
        if self._http:
            await self._http.aclose()

    async def check(self) -> bool:
        if not self._http:
            return False
        try:
            r = await self._http.get(f"{self.host}/api/tags")
            return r.status_code == 200
        except Exception:
            return False

    async def chat(self, messages: list[dict], **kwargs) -> str:
        if not self._http:
            return "Error: Ollama not connected."
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                }
            }
            r = await self._http.post(f"{self.host}/api/chat", json=payload)
            if r.status_code == 200:
                return r.json().get("message", {}).get("content", "")
            return f"Error: Ollama returned HTTP {r.status_code}"
        except Exception as e:
            log.error("Ollama chat error: %s", e)
            return f"Error: {e}"
