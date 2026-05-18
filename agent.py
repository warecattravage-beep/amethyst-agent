"""Onyx Agent - core reasoning loop with tool calling."""
from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from config import config
from memory import ConversationMemory, LongTermMemory, log_conversation
from tools import TOOL_REGISTRY, get_tool_specs, run_tool

logger = logging.getLogger("onyx")


class Agent:
    """Lightweight agent loop powered by Gemma 4 + Ollama."""

    def __init__(self):
        self.memory = ConversationMemory()
        self.ltm = LongTermMemory()
        self.tool_specs = get_tool_specs()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(self, user_input: str, stream: bool = False) -> str | None:
        """Process a user message and return (or stream) the agent's reply."""
        self.memory.add_user(user_input)

        # Check for long-term memory retrieval
        user_input = await self._augment_with_ltm(user_input)

        if stream:
            return await self._chat_stream(user_input)
        else:
            return await self._chat_once(user_input)

    async def reset(self):
        """Clear conversation history."""
        self.memory.clear()

    def get_history(self) -> list[dict]:
        return self.memory.to_ollama_format()

    # ------------------------------------------------------------------
    # Core loop
    # ------------------------------------------------------------------

    async def _chat_once(self, user_input: str, max_tool_rounds: int = 5) -> str:
        """Single (non-streaming) chat with tool-calling loop."""
        history = self.memory.to_ollama_format()
        messages = [
            {"role": "system", "content": self._system_prompt()},
            *history,
            {"role": "user", "content": user_input},
        ]

        for _ in range(max_tool_rounds):
            resp = await ollama_client.chat(
                messages=[],
                user_msg="",
                tools=self.tool_specs if self.tool_specs else None,
            )
            # Actually we need to handle this differently - pass full messages
            # Let's use the raw API
            resp = await self._raw_chat(messages)

            msg = resp.get("message", {})
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])

            if not tool_calls:
                # Final response - no more tools needed
                self.memory.add_assistant(content)
                log_conversation(self.memory.to_ollama_format())
                return content

            # Process tool calls
            for tc in tool_calls:
                func = tc.get("function", {})
                name = func.get("name", "")
                raw_args = func.get("arguments", {})

                # Ollama may return arguments as a JSON string
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        pass

                logger.info("Tool call: %s(%s)", name, raw_args)
                result = await run_tool(name, raw_args)
                logger.info("Tool result (truncated): %s…", result[:200])

                self.memory.add_tool_result(name, result)
                messages.append({
                    "role": "tool",
                    "name": name,
                    "content": result,
                })

        # Fallback if max tool rounds exhausted
        fallback = "I've reached the maximum number of tool calls. Let me summarize what I've done."
        self.memory.add_assistant(fallback)
        return fallback

    async def _raw_chat(self, messages: list[dict]) -> dict:
        """Raw Ollama API call."""
        payload = {
            "model": config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
            },
        }
        if self.tool_specs:
            payload["tools"] = self.tool_specs

        async with httpx.AsyncClient(base_url=config.ollama_host) as client:
            r = await client.post("/api/chat", json=payload, timeout=120)
            r.raise_for_status()
            return r.json()

    async def _chat_stream(self, user_input: str) -> None:
        """Streamed response (no tool calling in stream mode for simplicity)."""
        history = self.memory.to_ollama_format()
        messages = [
            {"role": "system", "content": self._system_prompt()},
            *history,
            {"role": "user", "content": user_input},
        ]

        import httpx
        payload = {
            "model": config.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
            },
        }

        collected = []
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
                        collected.append(content)
                        print(content, end="", flush=True)

        final = "".join(collected)
        self.memory.add_assistant(final)
        print()  # newline after stream

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _system_prompt(self) -> str:
        thinking = "<thinking>" if config.thinking else ""
        prompt = (
            f"{thinking}{config.system_prompt}\n\n"
            f"## Available Tools\n"
            f"You have access to the following tools. When you need to use one, "
            f"respond with a tool_call. Wait for the result before continuing.\n"
        )
        for spec in self.tool_specs:
            fn = spec.get("function", {})
            prompt += f"\n- **{fn.get('name')}**: {fn.get('description', 'No description')}"
        return prompt

    async def _augment_with_ltm(self, user_input: str) -> str:
        """Prepend relevant long-term memory to the user input."""
        # Simple keyword-based LTM retrieval
        words = set(user_input.lower().split())
        for key in self.ltm.list_keys():
            if any(w in key.lower() for w in words):
                content = self.ltm.read(key)
                if content:
                    return f"[Memory: {key}]\n{content}\n\n---\n\n{user_input}"
        return user_input
