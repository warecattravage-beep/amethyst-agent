"""Thin async Ollama client - chat & tool calls via REST API."""
from __future__ import annotations

import json
import sys
from typing import Any, AsyncGenerator

import httpx

from config import config


def _build_messages(
    system: str,
    history: list[dict],
    user_msg: str,
    thinking: bool,
) -> list[dict]:
    """Build the message array, inserting system prompt with thinking token."""
    thinking_token = "<thinking>" if thinking else ""
    messages = [
        {"role": "system", "content": f"{thinking_token}{system}"},
        *history,
        {"role": "user", "content": user_msg},
    ]
    return messages


def _build_payload(
    messages: list[dict],
    tools: list[dict] | None = None,
) -> dict:
    return {
        "model": config.model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
        },
    }


async def chat(
    history: list[dict],
    user_msg: str,
    tools: list[dict] | None = None,
) -> dict[str, Any]:
    """Single-turn chat. Returns the full Ollama response dict."""
    messages = _build_messages(config.system_prompt, history, user_msg, config.thinking)
    payload = _build_payload(messages, tools)

    async with httpx.AsyncClient(base_url=config.ollama_host) as client:
        r = await client.post("/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()


async def chat_stream(
    history: list[dict],
    user_msg: str,
    tools: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """Streamed chat. Yields content tokens as they arrive."""
    messages = _build_messages(config.system_prompt, history, user_msg, config.thinking)
    payload = _build_payload(messages, tools)
    payload["stream"] = True

    async with httpx.AsyncClient(base_url=config.ollama_host) as client:
        async with client.stream("POST", "/api/chat", json=payload, timeout=120) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content


async def list_models() -> list[str]:
    """Return list of available model names from Ollama."""
    async with httpx.AsyncClient(base_url=config.ollama_host) as client:
        r = await client.get("/api/tags")
        r.raise_for_status()
        data = r.json()
        return [m["name"] for m in data.get("models", [])]
