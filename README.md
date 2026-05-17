# ✦ Onyx Agent

Lightweight AI agent framework running **Gemma 4 E4B** via **Ollama** on Android (Termux) or any Linux device.

**Designed for:** Lenovo Yoga Tab 11 and similar Android tablets.

## Architecture

```
┌─────────────────────────────┐
│  Termux (Android)           │
│  ┌───────────────────────┐  │
│  │  Onyx Agent (Python)  │  │
│  │  ├─ Agent loop        │  │
│  │  ├─ Tool system       │  │
│  │  ├─ Memory (short+lt) │  │
│  │  └─ CLI/REPL          │  │
│  └─────────┬─────────────┘  │
│            │ REST API        │
│  ┌─────────▼─────────────┐  │
│  │  Ollama               │  │
│  │  └─ gemma4:e4b (4.5B) │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

## Features

- **Native function calling** — Gemma 4's built-in tool calling
- **Short-term memory** — rolling conversation context
- **Long-term memory** — persisted to `.md` files
- **6+ built-in tools** — shell, file I/O, web fetch, system info, notes
- **Plugin-ready** — drop a `.py` file into `plugins/` or `tools/`
- **Thinking mode** — Gemma 4's configurable reasoning tokens
- **REPL + single-shot** modes

## Quick Start (Termux on Android)

```bash
# 1. Copy the project to your tablet
#    (ADB, USB, Syncthing, or git clone)

# 2. Run the setup script
bash setup_termux.sh

# 3. Start Ollama in the background
ollama serve &

# 4. Launch Onyx
python cli.py
```

## Quick Start (Linux / Desktop)

```bash
# Install Ollama: https://ollama.com/download
ollama pull gemma4:e4b
ollama serve &

pip install httpx
python cli.py
```

## Usage

### Interactive REPL
```bash
python cli.py
╰─➤  what's the current system status?
╰─➤  /tools
╰─➤  /help
╰─➤  /quit
```

### Single turn
```bash
python cli.py "list all files in this directory"
```

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show commands |
| `/reset` | Clear conversation history |
| `/model <name>` | Switch models |
| `/tools` | List all available tools |
| `/config` | Show current config |
| `/quit` | Exit |

## Built-in Tools

- **shell** — Run shell commands on the device
- **read_file** — Read text files
- **write_file** — Write text files
- **web_fetch** — Fetch URLs
- **system_info** — Device CPU/memory/OS
- **save_note** — Quick persistent notes

## Adding Tools

Drop a Python file in `tools/` that exports:

```python
from tools import register_tool

async def my_handler(args: dict) -> str:
    return "result"

register_tool("my_tool", {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "What it does",
        "parameters": {"type": "object", "properties": {...}, "required": [...]},
    },
}, my_handler)
```

## Why Gemma 4 E4B?

| Property | Value |
|----------|-------|
| Effective params | 4.5B |
| Total params | ~8B (with embeddings) |
| Context | 128K tokens |
| Modalities | Text, Image, Audio |
| Function calling | ✅ Native |
| Thinking mode | ✅ Configurable |
| Designed for | Edge/mobile devices |

## License

MIT
