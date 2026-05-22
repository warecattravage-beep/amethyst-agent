"""Amethyst Agent - configuration"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    ollama_host: str = "http://localhost:11434"
    model: str = "gemma4:e4b"
    system_prompt: str = (
        "You are Amethyst, a capable AI agent running on a mobile device. "
        "You are helpful, efficient, and proactive. "
        "You have access to tools you can call to accomplish tasks. "
        "When you use a tool, wait for its result before continuing. "
        "Think step by step when solving complex problems."
    )
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 64
    max_tokens: int = 2048
    max_history: int = 20          # turns kept in short-term memory
    memory_dir: str = "memory"
    plugins_dir: str = "plugins"
    tools_dir: str = "tools"

    # Thinking mode - Gemma 4 supports configurable thinking
    thinking: bool = True
    # If set, persist conversation logs here
    log_file: Optional[str] = None


config = Config()
