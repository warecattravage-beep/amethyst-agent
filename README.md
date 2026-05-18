# ✦ Onyx Agent Gateway

**Standalone, cross-platform AI agent gateway.**
Multi-messenger, multi-model, plugin skills — all in one local app.

```
     ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
    ██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
    ██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝
    ██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗
    ╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
     ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝
     ✦ Agent Gateway ✦
```

## Features

- **Multi-messenger** — Console, Telegram, Discord (selectable)
- **Multi-model** — Ollama (local), OpenAI, Claude (switch anytime)
- **Plugin skills** — Coding, terminal, web search, web fetch
- **Dashboards** — Native GUI (Kivy) on desktop, Web UI on Termux/Android
- **Cross-platform** — Windows, Linux, Android (Termux)

## Quick Start

```bash
git clone https://github.com/warecattravage-beep/onyx-agent-v3.git
cd onyx-agent-v3
bash install.sh
python3 onyx.py setup
python3 onyx.py start
```

## Commands

| Command | What it does |
|---|---|
| `python3 onyx.py setup` | Setup wizard |
| `python3 onyx.py start` | Launch agent |
| `python3 onyx.py dashboard` | GUI dashboard (Kivy or Web) |
| `python3 onyx.py dashboard --web` | Force web dashboard |
| `python3 onyx.py status` | CLI overview |

## Architecture

```
onyx.py → OnyxEngine
            ├── messengers/    (console, telegram, discord)
            ├── models/        (ollama, openai)
            └── skills/        (coding, terminal, web, chat)

dashboard/
    ├── app.py          Kivy GUI (Windows/Linux)
    └── web_dashboard.py Web UI (Termux/Android)
```

## Messengers

Toggle on/off from the dashboard or `config.json`:

```json
"messengers": {
  "console":  {"enabled": true},
  "telegram": {"enabled": false, "token": "..."},
  "discord":  {"enabled": false, "token": "..."}
}
```

## Models

```json
"models": {
  "ollama": {"enabled": true,  "host": "http://localhost:11434", "model": "gemma2:9b"},
  "openai": {"enabled": false, "api_key": "", "model": "gpt-4o"}
}
```

## Skills

| Skill | Description |
|---|---|
| `chat` | General conversation (always on) |
| `coding` | Write + run Python, bash, node |
| `terminal` | Shell commands (blocklist-safe) |
| `web_search` | Brave / DuckDuckGo |
| `web_fetch` | Fetch any URL |

## License

MIT
