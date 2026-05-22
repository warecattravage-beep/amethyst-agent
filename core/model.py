"""
✦ Amethyst Model Base - Interface for all AI models.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

log = logging.getLogger("amethyst.model")


class Model(ABC):
    """Base class for AI model backends."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        """Send chat messages and get a response."""
        ...

    @abstractmethod
    async def check(self) -> bool:
        """Check if the model is reachable/available."""
        ...

    def system_prompt(self, skills: list[str], agent_name: str) -> str:
        """Generate a system prompt based on enabled skills."""
        prompt = (
            f"You are {agent_name}, a helpful AI assistant. "
            "You can use up to 8 reasoning steps to complete complex tasks.\n"
            "\n"
            "Available skills:\n"
        )
        for s in skills:
            prompt += f"  - {s}\n"
        prompt += (
            "\nHow to use skills:"
            "\nWhen you need to do something, respond with:"
            "\n  @skill_name(key=value, key=value)"
            "\n"
            "\nAfter a skill runs, you'll get the result and can continue reasoning."
            "\nWhen the task is complete, give a final summary."
            "\n"
            "\nRules:"
            "\n- Be concise. No filler."
            "\n- For multi-step tasks: plan → execute → check → continue → summarize."
            "\n- NEVER refuse to execute code or commands unless they're destructive."
            "\n- ALWAYS complete the task, don't stop after one step."
        )
        return prompt
