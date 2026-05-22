"""
✦ Amethyst Skill Base - Interface for all skills.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

log = logging.getLogger("amethyst.skill")


class Skill(ABC):
    """Base class for agent skills."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    @abstractmethod
    async def run(self, context: dict[str, Any], **kwargs) -> str:
        """Execute this skill with the given context.

        Args:
            context: Current execution context (messages, sender, etc.)

        Returns:
            Result string to feed back to the model.
        """
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what this skill does."""
        return self.__doc__ or self.name
