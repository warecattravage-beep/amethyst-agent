"""
✦ Onyx Model Base — Interface for all AI models.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

log = logging.getLogger("onyx.model")


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
            "You have access to the following skills:\n"
        )
        for s in skills:
            prompt += f"- {s}\n"
        prompt += (
            "\nRules:\n"
            "- Be concise and direct. No filler.\n"
            "- When you need to run code or access the system, use appropriate skill commands.\n"
            "- If a task requires a skill you don't have, say so clearly.\n"
        )
        return prompt
