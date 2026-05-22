#!/usr/bin/env python3
"""Amethyst Agent - CLI interface for Android Termux."""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent import Agent
from config import config
from tools import TOOL_REGISTRY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("amethyst")


async def interactive():
    """Interactive REPL mode."""
    agent = Agent()

    print("\n✦ Amethyst Agent - Gemma 4 E4B on Ollama")
    print(f"  Model: {config.model}")
    print(f"  Tools loaded: {len(TOOL_REGISTRY)}")
    print(f"  Thinking mode: {'ON' if config.thinking else 'OFF'}")
    print("  Type /help for commands, /quit to exit\n")

    while True:
        try:
            user_input = input("╰─➤  ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            result = handle_command(agent, user_input)
            if result == "quit":
                break
            continue

        print("  ", end="", flush=True)
        reply = await agent.chat(user_input, stream=False)
        print(f"  {reply}\n")


def handle_command(agent: Agent, cmd: str) -> str | None:
    cmd = cmd.lower()
    if cmd in ("/quit", "/exit", "/q"):
        print("  Goodbye.")
        return "quit"

    if cmd == "/reset":
        asyncio.create_task(agent.reset())
        print("  Conversation reset.\n")

    elif cmd.startswith("/model "):
        new_model = cmd[7:].strip()
        config.model = new_model
        print(f"  Model set to: {new_model}\n")

    elif cmd == "/tools":
        print(f"  Tools ({len(TOOL_REGISTRY)}):")
        for name, entry in TOOL_REGISTRY.items():
            desc = entry["spec"].get("function", {}).get("description", "")
            print(f"    • {name} - {desc}")
        print()

    elif cmd == "/help":
        print("""  Commands:
    /quit, /exit  - Quit
    /reset        - Clear conversation history
    /model <name> - Switch Ollama model
    /tools        - List available tools
    /help         - This message
    /config       - Show current config
""")

    elif cmd == "/config":
        print(f"""  Config:
    model:       {config.model}
    host:        {config.ollama_host}
    temperature: {config.temperature}
    top_p:       {config.top_p}
    thinking:    {config.thinking}
    max_tokens:  {config.max_tokens}
    tools:       {len(TOOL_REGISTRY)}
""")

    else:
        print(f"  Unknown command: {cmd}. Type /help\n")


async def single_turn(user_input: str):
    """Run a single turn and print the response."""
    agent = Agent()
    reply = await agent.chat(user_input, stream=False)
    print(reply)


def main():
    if len(sys.argv) > 1 and sys.argv[1] != "--interactive":
        user_msg = " ".join(sys.argv[1:])
        asyncio.run(single_turn(user_msg))
    else:
        asyncio.run(interactive())


if __name__ == "__main__":
    main()
