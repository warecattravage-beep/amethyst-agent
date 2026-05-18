"""
✦ Chat Skill - General conversation.
"""
from __future__ import annotations

import logging
from typing import Any

from core.skill import Skill

log = logging.getLogger("onyx.skill.chat")


class ChatSkill(Skill):
    """General conversation and Q&A. Always active as fallback."""

    def __init__(self, config: dict):
        super().__init__("chat", config)

    async def run(self, context: dict[str, Any], **kwargs) -> str:
        """Chat is handled by the model directly - no special execution needed."""
        return ""
