"""Built-in tools: shell, file ops, web fetch, system info."""
import asyncio
import subprocess
import tempfile
from pathlib import Path

from tools import register_tool

# ---------------------------------------------------------------------------
# Shell command
# ---------------------------------------------------------------------------

async def _shell_handler(args: dict) -> str:
    cmd = args.get("command", "")
    if not cmd:
        return "Error: empty command"
    timeout = args.get("timeout", 15)
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=timeout,
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode(errors="replace").strip()
        err = stderr.decode(errors="replace").strip()
        parts = []
        if out:
            parts.append(out)
        if err:
            parts.append(f"[stderr] {err}")
        return "\n".join(parts) if parts else "(no output)"
    except asyncio.TimeoutError:
        return f"Error: command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"

register_tool("shell", {
    "type": "function",
    "function": {
        "name": "shell",
        "description": "Run a shell command on the device. Use with caution.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 15)",
                },
            },
            "required": ["command"],
        },
    },
}, _shell_handler)

# ---------------------------------------------------------------------------
# Read file
# ---------------------------------------------------------------------------

async def _read_handler(args: dict) -> str:
    path = Path(args["path"])
    if not path.exists():
        return f"Error: file not found: {path}"
    try:
        return path.read_text(errors="replace")
    except Exception as e:
        return f"Error reading file: {e}"

register_tool("read_file", {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a text file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file",
                },
            },
            "required": ["path"],
        },
    },
}, _read_handler)

# ---------------------------------------------------------------------------
# Write file
# ---------------------------------------------------------------------------

async def _write_handler(args: dict) -> str:
    path = Path(args["path"])
    content = args["content"]
    mode = args.get("mode", "w")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content) if mode == "w" else path.write_text(content, encoding="utf-8")
        return f"Written {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

register_tool("write_file", {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write text content to a file (overwrites by default).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to write to",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write",
                },
                "mode": {
                    "type": "string",
                    "enum": ["w", "a"],
                    "description": "Write or append mode",
                },
            },
            "required": ["path", "content"],
        },
    },
}, _write_handler)

# ---------------------------------------------------------------------------
# Web fetch
# ---------------------------------------------------------------------------

async def _fetch_handler(args: dict) -> str:
    url = args["url"]
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=30, follow_redirects=True)
            r.raise_for_status()
            text = r.text
            if len(text) > 4000:
                text = text[:4000] + "\n...(truncated)"
            return text
    except Exception as e:
        return f"Error fetching {url}: {e}"

register_tool("web_fetch", {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": "Fetch and return the contents of a URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "HTTP or HTTPS URL to fetch",
                },
            },
            "required": ["url"],
        },
    },
}, _fetch_handler)

# ---------------------------------------------------------------------------
# System info
# ---------------------------------------------------------------------------

async def _sysinfo_handler(_args: dict) -> str:
    import platform
    info = {
        "platform": platform.platform(),
        "processor": platform.processor() or "N/A",
        "hostname": platform.node(),
        "python": platform.python_version(),
    }
    try:
        import psutil
        mem = psutil.virtual_memory()
        info["memory_used_mb"] = round((mem.total - mem.available) / 1024 / 1024, 1)
        info["memory_total_mb"] = round(mem.total / 1024 / 1024, 1)
        cpu = psutil.cpu_percent(interval=0.5)
        info["cpu_percent"] = cpu
    except ImportError:
        info["memory"] = "psutil not available"
    return "\n".join(f"{k}: {v}" for k, v in info.items())

register_tool("system_info", {
    "type": "function",
    "function": {
        "name": "system_info",
        "description": "Get device system information (OS, CPU, memory, Python version).",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}, _sysinfo_handler)

# ---------------------------------------------------------------------------
# Note (quick memory save)
# ---------------------------------------------------------------------------

async def _note_handler(args: dict) -> str:
    content = args["content"]
    path = Path("memory") / "scratch_notes.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n")
    return f"Note saved to {path}"

register_tool("save_note", {
    "type": "function",
    "function": {
        "name": "save_note",
        "description": "Save a quick note to agent memory (persistent scratch pad).",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to remember",
                },
            },
            "required": ["content"],
        },
    },
}, _note_handler)

# ── Moltbook social network ──────────────────────────────────────────
import tools.moltbook  # noqa: F401
