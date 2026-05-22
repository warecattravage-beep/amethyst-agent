"""Built-in tools for the Amethyst agent.

Each tool module exports:
- `tool_spec` - JSON schema dict (Ollama tools format)
- `handler(request: dict) -> str` - async callable returning result text
"""

from typing import Any

TOOL_REGISTRY: dict[str, Any] = {}


def register_tool(name: str, spec: dict, handler):
    TOOL_REGISTRY[name] = {"spec": spec, "handler": handler}


def get_tool_specs() -> list[dict]:
    return [entry["spec"] for entry in TOOL_REGISTRY.values()]


async def run_tool(name: str, arguments: dict) -> str:
    entry = TOOL_REGISTRY.get(name)
    if not entry:
        return f"Error: unknown tool '{name}'"
    try:
        result = await entry["handler"](arguments)
        return str(result)
    except Exception as e:
        return f"Error running tool '{name}': {e}"
